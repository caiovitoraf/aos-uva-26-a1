from dataclasses import dataclass, field
from functools import cmp_to_key
from typing import Iterable


@dataclass
class ContadorPassos:
    etapas: dict[str, int] = field(default_factory=dict)

    def contar(self, etapa: str, quantidade: int = 1) -> None:
        if quantidade:
            self.etapas[etapa] = self.etapas.get(etapa, 0) + quantidade

    @property
    def total(self) -> int:
        return sum(self.etapas.values())


def ordenar_com_passos(valores: Iterable[str], contador: ContadorPassos | None) -> list[str]:
    if contador is None:
        return sorted(valores)

    def comparar(a: str, b: str) -> int:
        # Conta cada comparação < ou > entre strings, não seus caracteres internos.
        contador.contar("Comparações entre textos na ordenação")
        if a < b:
            return -1
        contador.contar("Comparações entre textos na ordenação")
        if a > b:
            return 1
        return 0

    return sorted(valores, key=cmp_to_key(comparar))
