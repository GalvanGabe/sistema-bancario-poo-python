from abc import ABC, abstractmethod
from datetime import datetime
import textwrap

class Cliente:
    def __init__(self, endereco):
        self.endereco = endereco
        self.contas = []

    def realizar_transacao(self, conta, transacao):
        return transacao.registrar(conta)

    def adicionar_conta(self, conta):
        self.contas.append(conta)

class PessoaFisica(Cliente):
    def __init__(self, endereco, nome, data_nascimento, cpf):
        super().__init__(endereco)
        self.nome = nome
        self.data_nascimento = data_nascimento
        self.cpf = cpf

class Conta:
    def __init__(self, numero, cliente):
        self._saldo = 0
        self._numero = numero
        self._agencia = "0001"
        self._cliente = cliente
        self._historico = Historico()

    @classmethod
    def nova_conta(cls, cliente, numero):
        return cls(numero, cliente)
    
    @property
    def saldo(self):
        return self._saldo
    
    @property
    def numero(self):
        return self._numero
    
    @property
    def agencia(self):
        return self._agencia
    
    @property
    def cliente(self):
        return self._cliente
    
    @property
    def historico(self):
        return self._historico
    
    def sacar(self, valor):
        if valor <= 0:
            return False
        
        if valor > self._saldo:
            return False
        
        self._saldo -= valor
        return True
    
    def depositar(self, valor):
        if valor <= 0:
            return False
        
        self._saldo += valor
        return True
class ContaCorrente(Conta):
    def __init__(self, numero, cliente, limite=500, limite_saques=3):
        super().__init__(numero, cliente)
        self.limite = limite
        self.limite_saques = limite_saques

    def sacar(self, valor):
        if valor <= 0:
            return False
        
        numero_saques = len([
            transacao for transacao in self.historico.transacoes if transacao["tipo"] == Saque.__name__
        ])

        if valor > self.limite:
            return False
        
        if numero_saques >= self.limite_saques:
            return False
        
        return super().sacar(valor)
    
    def __str__(self):
        return f"""\
            Agência:\t{self.agencia}
            C/C:\t\t{self.numero}
            Titular:\t{self.cliente.nome}
        """
    
class Historico:
    def __init__(self):
        self._transacoes = []

    @property
    def transacoes(self):
        return self._transacoes
    
    def adicionar_transacao(self, transacao):
        self._transacoes.append(
            {
                "tipo": transacao.__class__.__name__,
                "valor": transacao.valor,
                "data": datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
            }
        )

class Transacao(ABC):
    @property
    @abstractmethod
    def valor(self):
        pass

    @abstractmethod
    def registrar(cls, conta):
        pass

class Saque(Transacao):
    def __init__(self, valor):
        self._valor = valor

    @property
    def valor(self):
        return self._valor
    
    def registrar(self, conta):
        sucesso_transacao = conta.sacar(self.valor)

        if sucesso_transacao:
            conta.historico.adicionar_transacao(self)

        return sucesso_transacao

class Deposito(Transacao):
    def __init__(self, valor):
        self._valor = valor

    @property
    def valor(self):
        return self._valor

    def registrar(self, conta):
        sucesso_transacao = conta.depositar(self.valor)

        if sucesso_transacao:
            conta.historico.adicionar_transacao(self)

        return sucesso_transacao

def menu():
    menu = """\n
    ================= MENU ================
    [d]\tDepositar
    [s]\tSacar
    [e]\tExtrato
    [nc]\tNova Conta
    [lc]\tListar Contas
    [nu]\tNovo Usuário
    [q]\tSair
    ==>  """
    return input(textwrap.dedent(menu))

def filtrar_cliente(cpf, clientes):
    clientes_filtrados = [cliente for cliente in clientes if cliente.cpf == cpf]
    return clientes_filtrados[0] if clientes_filtrados else None

def recuperar_conta_cliente(cliente):
    if not cliente.contas:
        mensagem("Cliente não possui conta!", "erro")
        return None
    
    # FIXME: não permite cliente escolher a conta
    return cliente.contas[0]

def depositar(clientes):
    cliente = obter_cliente(clientes)

    if not cliente:
        return
    
    valor = float(input("Informe o valor do depósito: "))
    transacao = Deposito(valor)

    conta = recuperar_conta_cliente(cliente)
    if not conta:
        return
    
    sucesso = cliente.realizar_transacao(conta, transacao)

    if sucesso:
        mensagem("Depósito realizado com sucesso!", "sucesso")
    else:
        mensagem("Operação falhou! Valor inválido.", "erro")

def sacar(clientes):
    cliente = obter_cliente(clientes)

    if not cliente:
        return
    
    valor = float(input("Informe o valor do saque: "))
    transacao = Saque(valor)

    conta = recuperar_conta_cliente(cliente)
    if not conta:
        return
    
    sucesso = cliente.realizar_transacao(conta, transacao)

    if sucesso:
        mensagem("Saque realizado com sucesso!", "sucesso")
    else:
        mensagem("Operação falhou!, Verifique saldo ou limite.", "erro")

def exibir_extrato(clientes):
    cliente = obter_cliente(clientes)

    if not cliente:
        return
    
    conta = recuperar_conta_cliente(cliente)
    if not conta:
        return
    
    mensagem("========== EXTRATO ==========", "info")
    transacoes = conta.historico.transacoes

    extrato = ""
    if not transacoes:
        mensagem("Não foram realizadas movimentações.", "info")
    else:
        for transacao in transacoes:
            extrato += f"\n{transacao['tipo']}:\n\tR${transacao['valor']:.2f}"

    print(f"\nSaldo:\n\tR$ {conta.saldo:.2f}")

def criar_cliente(clientes):
    cpf = input("Informe o CPF (somente números): ")
    cliente = filtrar_cliente(cpf, clientes)

    if cliente:
        mensagem("Já existe cliente com esse CPF!", "erro")
        return
    
    nome = input("Informe o seu nome completo: ")
    data_nascimento = input("Informe a sua data de nascimento (dd-mm-aaaa): ")
    endereco = input("Informe o seu endereço (logradouro, nro - bairro - cidade/sigla estado): ")

    cliente = PessoaFisica(nome=nome, data_nascimento=data_nascimento, cpf=cpf, endereco=endereco)

    clientes.append(cliente)

    mensagem("Cliente criado com sucesso!", "sucesso")

def criar_conta(numero_conta, clientes, contas):
    cliente = obter_cliente(
        clientes,
        mensagem_erro="Cliente não encontrado, fluxo de criação de conta encerrado!",
    )

    if not cliente:
        return
    
    conta = ContaCorrente.nova_conta(cliente=cliente, numero=numero_conta)
    contas.append(conta)
    cliente.contas.append(conta)

    mensagem("Conta criada com sucesso!", "sucesso")

def listar_contas(contas):
    for conta in contas:
        print("=" * 100)
        print(textwrap.dedent(str(conta)))

def obter_cliente(clientes, mensagem_erro="Cliente não encontrado!"):
    cpf = input("Informe o CPF do cliente: ")
    cliente = filtrar_cliente(cpf, clientes)

    if not cliente:
        mensagem(mensagem_erro, "erro")
        return None
    
    return cliente

def mensagem(texto, tipo="info"):
    tipos = {
        "sucesso": f"\n=== {texto} ===",
        "erro": f"\n@@@ {texto} @@@",
        "info": f"\n{texto}"
    }

    print(tipos.get(tipo, tipos["info"]))

def main():
    clientes = []
    contas = []

    while True:
        opcao = menu()

        if opcao == "d":
            depositar(clientes)
        elif opcao == "s":
            sacar(clientes)
        elif opcao == "e":
            exibir_extrato(clientes)
        elif opcao == "nu":
            criar_cliente(clientes)
        elif opcao == "nc":
            numero_conta = len(contas) + 1
            criar_conta(numero_conta, clientes, contas)
        elif opcao == "lc":
            listar_contas(contas)
        elif opcao == "q":
            break
        else:
            mensagem("Operação inválida, por favor selecione novamente a operação desejada.", "erro")

main()