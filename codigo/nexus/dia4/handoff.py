"""A mesma equipe sem supervisor: cada agente transfere para o proximo."""
from typing import Annotated

from langchain_core.messages import ToolMessage
from langchain_core.tools import InjectedToolCallId, tool
from langgraph.prebuilt import InjectedState
from langgraph.types import Command


def criar_handoff(destino: str, quando: str):
    """Fabrica uma ferramenta de transferencia para outro agente do grafo pai."""

    @tool(f"transferir_para_{destino}", description=quando)
    def ferramenta(
        motivo: Annotated[str, "Por que esta transferencia e necessaria agora"],
        state: Annotated[dict, InjectedState],
        tool_call_id: Annotated[str, InjectedToolCallId],
    ) -> Command:
        recibo = ToolMessage(content=f"Transferido para {destino}. Motivo: {motivo}",
                             name=f"transferir_para_{destino}",
                             tool_call_id=tool_call_id)
        return Command(
            goto=destino,
            graph=Command.PARENT,
            update={"messages": state["messages"] + [recibo], "agente_ativo": destino},
        )

    return ferramenta


para_analista = criar_handoff(
    "analista",
    "Transfira para o analista quando ja houver fatos e numeros brutos que precisam "
    "de calculo ou comparacao.")
para_redator = criar_handoff(
    "redator",
    "Transfira para o redator quando a pesquisa e a analise estiverem completas e "
    "houver material suficiente para escrever o relatorio.")
para_pesquisador = criar_handoff(
    "pesquisador",
    "Transfira para o pesquisador quando faltar algum fato ou fonte nos documentos.")
