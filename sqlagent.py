from langchain_openai import ChatOpenAI
from langchain_community.agent_toolkits.sql.base import create_sql_agent
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain_core.messages import SystemMessage


# Carregando variavies de ambiente
from dotenv import load_dotenv
import os
load_dotenv()

# Criando classe de estado para o LangGraph
class Estado(TypedDict):
    pergunta: str  # Pergunta do usuário
    status: Optional[str]  # Status da execução ("sucesso", "checking" "erro")
    mensagem: Optional[str]  # Mensagem de erro ou sucesso
    resultado: Optional[str]  # Resultado da pergunta

#Configuração de acesso ao banco Postgree. Dados sensiveis adicionados em .env para evitar exposição atoa.
uri_db = f'{os.getenv("DB_TYPE")}+{os.getenv("DB_LIBRARY")}://{os.getenv("DB_USER")}:{os.getenv("DB_PASS")}@{os.getenv("DB_HOST")}/{os.getenv("DB_DATABASE")}'
db = SQLDatabase.from_uri(uri_db, schema = "public")

#Modelo também configurado via .env
model= ChatOpenAI(model = os.getenv("MODEL_AI"), temperature=0)

toolkit = SQLDatabaseToolkit(db=db, llm = model)

agent_executor = create_sql_agent(
    llm=model,
    toolkit = toolkit, 
    verbose = True,
    
)
# Criação dos Nós do LangGraph
# Nó 1: Verificação de SQL Injection
# Codigo direto para verificar se já veio com algum SQLInjection na mensangem 
def fun_check_sql_injection(estado: Estado)-> Estado:
    """
    Essa função vai verificar se é um comando direto de alteração de banco de dados dentro da pergunta.
    """
    print("Executando o Nó - check_sql_injection")
    # Lista de palavras-chave suspeitas
    palavras_suspeitas = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", ";", "--"]
    
    # Verificar se a pergunta contém palavras suspeitas
    if any(palavra in estado["pergunta"].upper() for palavra in palavras_suspeitas):
        estado["status"] = "erro"
        estado["mensagem"] = "Possível tentativa de SQL Injection detectada."
    else:
        estado["status"] = "checking"
    return estado

# Nó2 Criado também um agente com prompt proprio para tentar verficar SQLInjection através do uso da LLM
def fun_check_sql_injection_using_model(estado: Estado)-> Estado:
    '''
    Essa função irá utilizar do modelo para tentar previnir perguntas maliciosas pedindo para alterar o banco.
    Usando um prompt especifico para essa função é pedido para o retorno de NAO ou SIM
    Caso o modelo ache que o pergunta tem um pedido malicioso.
    '''
    print("Executando o Nó - check_sql_injection_using_model")
    
    system_message =''''
    Você é um verificar de mensagens inteligente no qual verifica se a pergunta recebida pode gerar SQLInjection atravês de perguntas maliciosas.
    Como pedidos para MODIFICAR, ALTERAR, EXCLUIR, DELETAR informaçoes de CLIENTES , TRANSACOES e PRODUTOS do banco.
    Caso ache que o a pergunta pode modificar o banco de dados retorne somente a palavra SIM em maiusculo.
    Caso ache que a pergunta sem SQLInjection, retorne somente a palavra NAO em maiusculo. 
    '''

    template = [
        SystemMessage(content=system_message), 
        ("human","{pergunta_usuario}") #Usado em forma de tupla para passar a pergunta
        ]
    prompt_template  = ChatPromptTemplate.from_messages(template)

    chain = prompt_template | model | StrOutputParser()

    result = chain.invoke({"pergunta_usuario":estado["pergunta"]})
    if "NAO" in result:
        estado["status"] = "sucesso"
    else: 
        estado["status"] = "erro"
        estado["mensagem"] = "Possível tentativa de SQL Injection detectada (usando Model)."
    return estado    

# Nó 3: Execução da pergunta do usuario caso passe pelos 2 primeiros nós
def fun_execute_agent(estado : Estado):
    """
    Essa função vai executar de fato a questão do usuario utilizando do agent SQL
    """
    print("Executando o Nó - execute_agent")
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
def fun_result_to_user(estado):
    """
    Essa função irá retornar ou a resposta do modelo ou a mensagem de erro das funçoes de verificação
    """
    if estado["status"] =="erro":
        print(estado["mensagem"])
    else:
        print( estado["resultado"])
    return estado

# Função de condição para arestas condicionais
def fun_decide_next_node_1(estado: Estado) -> str:
    """
    Decide para qual nó o fluxo deve seguir com base no estado.
    """
    if "erro" in estado["status"] :
        return "result_to_user"  # Vai direto para o fim em caso de erro
    else:
        return "check_sql_injection_using_model"  # Continua o fluxo normal
    
# Função de condição para arestas condicionais
def fun_decide_next_node_2(estado: Estado) -> str:
    """
    Decide para qual nó o fluxo deve seguir com base no estado.
    """
    if "erro" in estado["status"] :
        return "result_to_user"  # Vai direto para o fim em caso de erro
    else:
        return "execute_agent"  # Continua o fluxo normal    

# Criar o grafo
grafo = StateGraph(Estado)

# Adicionar nós ao grafo
grafo.add_node("check_sql_injection", fun_check_sql_injection)
grafo.add_node("check_sql_injection_using_model", fun_check_sql_injection_using_model)
grafo.add_node("execute_agent", fun_execute_agent)
grafo.add_node("result_to_user", fun_result_to_user)

# Definir as arestas (fluxo)
grafo.add_edge("execute_agent","result_to_user")
grafo.add_edge("result_to_user", END)


# Adicionar aresta condicional após o nó `result_to_user`
grafo.add_conditional_edges(
    "check_sql_injection",
    fun_decide_next_node_1,  # Função que decide o próximo nó
    {
        "result_to_user": "result_to_user",  # caso de erro
        "check_sql_injection_using_model": "check_sql_injection_using_model"  # Continua o fluxo normal 
    }
)
grafo.add_conditional_edges(
    "check_sql_injection_using_model",
    fun_decide_next_node_2,  # Função que decide o próximo nó
    {
        "result_to_user":"result_to_user",  # Vai para o fim em caso de erro
        "execute_agent": "execute_agent"  # Continua o fluxo normal 
    }
)

# Definir o ponto de entrada do grafo
grafo.set_entry_point("check_sql_injection")

# Compilar o grafo
fluxo = grafo.compile()  


def faca_sua_pergunta(pergunta:str, comentario_teste:str = None):
    '''
    Função para testar / utilizar o SQLAgent
        :param pergunta: String com a pergunta
        :param comentario_teste: Comentário para imprimir junto.
    ''' 
    if comentario_teste:
        print(10*'-')
        print(comentario_teste)
        print(10*'-')
    try:    
        if isinstance(pergunta, str):
            print(f"Pergunta:{pergunta} ")
            fluxo.invoke({"pergunta":pergunta}) 
        else:
            print("Uma str é esperada")
        print("\n\n")
    except Exception as e:
        print("Erro durante a execução")
        print(e)        
