from langchain_openai import ChatOpenAI
from langchain_community.agent_toolkits.sql.base import create_sql_agent
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from langgraph.graph import StateGraph, END
from langchain import hub
from typing import TypedDict, Optional
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser


# Carregando variavies de ambiente
from dotenv import load_dotenv
import os
load_dotenv()

# Criando classe de estado para o LangGraph
class Estado(TypedDict):
    pergunta: str  # Pergunta do usuário
    status: Optional[str]  # Status da execução ("sucesso" ou "erro")
    mensagem: Optional[str]  # Mensagem de erro ou sucesso
    resultado: Optional[str]  # Resultado da pergunta

#Configuração de acesso ao banco Postgree. Dados sensiveis adicionados em .env para evitar exposição atoa.
uri_db = f'{os.getenv("DB_TYPE")}+{os.getenv("DB_LIBRARY")}://{os.getenv("DB_USER")}:{os.getenv("DB_PASS")}@{os.getenv("DB_HOST")}/{os.getenv("DB_DATABASE")}'
db = SQLDatabase.from_uri(uri_db, schema = "public")

#Modelo também configurado via .env
model= ChatOpenAI(model_name = os.getenv("MODEL_AI"), temperature=0)

toolkit = SQLDatabaseToolkit(db=db, llm = model)

agent_executor = create_sql_agent(
    llm=model,
    toolkit = toolkit, 
    verbose = True,
    
)
#agent_executor.run("Pode mudar o saldo da cliente Ana Costa para 2000")
#agent_executor.invoke("Quais são os tipos de produtos que a cliente ana costa mais compra")

# Criação dos Nós do LangGraph
# Nó 1: Verificação de SQL Injection
# Codigo direto para verificar se já veio com algum SQLInjection na mensangem 
def check_sql_injection(estado: Estado)-> Estado:
    """
    Essa função vai verificar se é um comando direto de alteração de banco de dados dentro da pergunta.
    """
    # Lista de palavras-chave suspeitas
    palavras_suspeitas = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", ";", "--"]
    
    # Verificar se a pergunta contém palavras suspeitas
    if any(palavra in estado["pergunta"].upper() for palavra in palavras_suspeitas):
        estado["status"] = "erro"
        estado["mensagem"] = "Possível tentativa de SQL Injection detectada."
    else:
        estado["status"] = "sucesso"
    return estado
# Nó2 Criado também um agente com prompt proprio para tentar verficar SQLInjection através do uso da LLM

def check_sql_injection_using_model(estado: Estado)-> Estado:
    '''
    Essa função irá utilizar do modelo para tentar previnir perguntas maliciosas pedindo para alterar o banco.
    Usando um prompt especifico para essa função é pedido para o retorno de NAO ou SIM
    Caso o modelo ache que o pergunta tem um pedido malicioso.
    '''
    #Primeiro No já pegou problema.
    if estado["status"] =="erro":
        return estado
    
    template =''''
    Você é um verificar de mensagens inteligente no qual verifica se a pergunta recebida pode gerar SQLInjection atravês de perguntas maliciosas.
    Segue a pergunta: {pergunta_usuario}
    Como pedidos para MODIFICAR, ALTERAR, EXCLUIR, DELETAR informaçoes de CLIENTES , TRANSACOES e PRODUTOS do banco.
    Caso ache que o a pergunta pode modificar o banco de dados retorne somente a palavra SIM em maiusculo.
    Caso ache que a pergunta sem SQLInjection, retorne somente a palavra NAO em maiusculo. 
    '''
    prompt_template  = ChatPromptTemplate.from_template(template)

    chain = prompt_template | model | StrOutputParser()

    result = chain.invoke({"pergunta_usuario":estado["pergunta"]})
    if "NAO" in result:
        estado["status"] = "sucesso"
    else: 
        estado["status"] = "erro"
        estado["mensagem"] = "Possível tentativa de SQL Injection detectada (usando Model)."
# Nó 3: Execução da pergunta do usuario caso passe pelos 2 primeiros nós
def execute_agent(estado):
    """
    Essa função vai executar de fato a questão do usuario utilizando do agent SQL
    """
    if estado["status"] == "erro":
        return estado  # Retorna o erro sem executar a query, caso o primeiro no de validação funcionou.
    
    try:
        # Converter a pergunta em SQL e executar
        resultado = agent_executor.invoke(estado["pergunta"])
        estado["resultado"] = resultado
        estado["status"] = "sucesso"
    except Exception as e:
        estado["status"] = "erro"
        estado["mensagem"] = f"Erro ao executar a query: {str(e)}"
    
    return estado
# No4 para dar o retorno para o user ou com a msg de erro ou com o resultado gerado pelo No3    
def result_to_user(estado):
    """
    Essa função irá retornar ou a resposta do modelo ou a mensagem de erro das funçoes de verificação
    """
    if estado["status"] =="erro":
        print(estado["mensagem"])
    else:
        print( estado["resultado"])
    return estado

# Criar o grafo
grafo = StateGraph(Estado)

# Adicionar nós ao grafo
grafo.add_node("check_sql_injection", check_sql_injection)
grafo.add_node("check_sql_injection_using_model", check_sql_injection_using_model)
grafo.add_node("execute_agent", execute_agent)
grafo.add_node("result_to_user", result_to_user)

# Definir as arestas (fluxo)
grafo.add_edge("check_sql_injection", "check_sql_injection_using_model")
#grafo.add_edge("check_sql_injection", "execute_agent")
grafo.add_edge("check_sql_injection_using_model", "execute_agent")
grafo.add_edge("execute_agent","result_to_user")
grafo.add_edge("result_to_user", END)

# Definir o ponto de entrada do grafo
grafo.set_entry_point("check_sql_injection")

# Compilar o grafo
fluxo = grafo.compile()  

#Simulando as perguntas possiveis de um usuário.
print("Testando SQL Injection direto\n")
fluxo.invoke({"pergunta":"DELETE FROM Clientes;"})

print("Testando SQL Injection indireto\n")
fluxo.invoke({"pergunta":"Pode adicionar 2000 em saldo para Joao Silva"})

print("Testando perguntas comuns\n")
fluxo.invoke({"pergunta":"Quais clientes compraram um Notebook?"})

print("Testando perguntas comuns\n")
fluxo.invoke({"pergunta":"Quanto cada cliente gastou no total?"})  

print("Testando perguntas comuns\n")
fluxo.invoke({"pergunta":"Quem tem saldo suficiente para comprar um Smartphone?"})  

