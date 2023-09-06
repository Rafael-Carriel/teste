import cplex
import numpy as np
import sys
import os


def decomposicao_LU(matriz):
    n = len(matriz)
    if len(matriz) != len(matriz[0]):
        raise ValueError("A matriz deve ser quadrada para a decomposição LU")

    L = np.zeros((n, n))
    U = np.zeros((n, n))

    for i in range(n):
        L[i][i] = 1

        for j in range(i, n):
            soma = 0
            for k in range(i):
                soma += L[i][k] * U[k][j]
            U[i][j] = matriz[i][j] - soma

        for j in range(i + 1, n):
            soma = 0
            for k in range(i):
                soma += L[j][k] * U[k][i]
            L[j][i] = (matriz[j][i] - soma) / U[i][i]

    return L, U

def resolver_sistema(L, U, b):
    n = len(L)
    y = np.zeros(n)
    x = np.zeros(n)

    for i in range(n):
        y[i] = b[i]
        for j in range(i):
            y[i] -= L[i][j] * y[j]
        y[i] /= L[i][i]
        
    for i in range(n - 1, -1, -1):
        x[i] = y[i]
        for j in range(i + 1, n):
            x[i] -= U[i][j] * x[j]
        x[i] /= U[i][i]

    return x

def matriz_inversa(matriz):
    L, U = decomposicao_LU(matriz)

    n = len(matriz)
    identidade = np.identity(n)
    inversa = np.zeros((n, n))

    for i in range(n):
        coluna_identidade = identidade[:, i]
        solucao = resolver_sistema(L, U, coluna_identidade)
        inversa[:, i] = solucao

    return inversa

def lerArquivoLP(lp_file_path):
    cpx = cplex.Cplex()
    cpx.read(lp_file_path)
    quantidadeartificiais = 0
    num_Restricoes = cpx.linear_constraints.get_num()
    num_Variaveis = cpx.variables.get_num()
    matrizA = [[0 for y in range(num_Variaveis)] for x in range(num_Restricoes)]
    b = [0 for x in range(num_Restricoes)]
    objetivo = []
    
    #Pegar funcao objetivo
    for j in range(num_Variaveis):
        objetivo.append(cpx.objective.get_linear(j))

    # Verifica se o modelo é de maximização ou minimização
    if cpx.objective.get_sense() == cpx.objective.sense.maximize:
        sentidoOriginal = "maximize"
        for j in range(num_Variaveis):
            objetivo[j] *= -1
    else:
        sentidoOriginal= "minimize"

    for i in range(num_Restricoes):
        b[i] = cpx.linear_constraints.get_rhs(i)

    #Pegar restricoes tecnicas
    sen = [" "] * num_Restricoes

    for i in range(num_Restricoes):
        lin_expr = cpx.linear_constraints.get_rows(i)
        lin_expr = [(n,m) for n,m in zip(lin_expr.ind,lin_expr.val)]
        for j in lin_expr:
            matrizA[i][j[0]]=j[1]
        
        sentido = cpx.linear_constraints.get_senses(i)
        sen
        #folga
        if b[i] < 0:
            if sentido == "L":
                sentido = "G"
            elif sentido == "G":
                sentido = "L"
            b[i] = b[i] * -1
            for j in range(len(matrizA[i])):
                matrizA[i][j] = matrizA[i][j] * -1
        if sentido == "E":
            quantidadeartificiais +=1
        if sentido == "G":
            quantidadeartificiais += 1
        sen[i] = sentido
        for x in range(num_Restricoes):
            matrizA[x].append(0)
        matrizA[i][-1]=1
        objetivo.append(0)

    #printar o problema já na forma padrão
    # print(b)
    # print(objetivo)
    # print(matrizA)
    # print("quantidade de artificiais: ", quantidadeartificiais)

    return sen, quantidadeartificiais, sentidoOriginal, objetivo, matrizA, b, num_Variaveis, num_Restricoes

def artificial(sentido, objetivo, quantidadeartificiais, matrizA, b, num_Variaveis, Num_restricoes):
    novo_objetivo = [0] * len(objetivo)
    print(sentido)
    for i in range(quantidadeartificiais):
        novo_objetivo.append(1)
    print("novo objetivo = ", novo_objetivo)

    for i in range(len(sentido)):
        if sentido[i] == 'G' or sentido[i] == 'E':
            nova_coluna = [1 if j == i else 0 for j in range(len(matrizA))]
            for row in matrizA:
                row.append(nova_coluna.pop(0))
    print("Matriz após adc as variaveis artificiais = ",matrizA)

    matrizB= []
    matrizNB = []
    custob = []
    custonb = []

    for x in range(len(novo_objetivo)):
        if novo_objetivo[x] == 1:
            matrizB.append([matrizA[i][x] for i in range(len(matrizA))])
            custob.append(novo_objetivo[x])

    for x in range(num_Variaveis + quantidadeartificiais, ((len(matrizA[0]) - quantidadeartificiais))):
        matrizB.append([matrizA[i][x] for i in range(len(matrizA))])
        custob.append(novo_objetivo[x])


    for x in range(0, num_Variaveis):
        matrizNB.append([matrizA[i][x] for i in range(len(matrizA))])
        custonb.append(novo_objetivo[x])
    print("matriz nao basicas = ", matrizNB)
    for x in range(num_Variaveis + len(matrizB[0]) - 1, len(matrizA[0]) - quantidadeartificiais):
        matrizNB.append([matrizA[i][x] for i in range(len(matrizA))])
        custonb.append(novo_objetivo[x])
    matrizNB = np.transpose(matrizNB)   
    # print("matriz nao basicas = ", matrizNB)
    # print("custonb = ", custonb) 
    # print("matriz basicas = ", matrizB)
    # print("custob = ", custob)

      
    interacao = 0
    while(True | interacao < 10):
        maior = 0
        quementranabase = 0
        print("matriz NB = ", matrizNB)
        print("matriz B = ", matrizB)
        inversa = matriz_inversa(matrizB)
        #inversa = np.linalg.inv(matrizB)
        print("inversa = ", inversa)
        custos = [0] * len(matrizNB[0])
        quementranabase = 0
        xb = multiplicamatriz(inversa, b)
        print("xb = ", xb)
        multiplicador = multiplicadorsimplex(inversa, custob)
        print("lambda = ", multiplicador, "\n")
        print("matriz = ", matrizNB)
        for i in range(len(custonb)):
            aux = [0] * len(matrizNB)
            for k in range(len(matrizNB)):
                aux[k] = matrizNB[k][i]
            print("custo não basico = ", custonb[i], " multiplicador = ", multiplicador, " matriznb = ", aux)
            custos[i] = custo(custonb[i], multiplicador, aux)

        if all(x >= 0 for x in custos):
            print("entrou aqui")
            print("custob =", custob)
            for i in custob:
                if i == 1:
                    print("RETORNANDO AQUIIIIIIIIIIIIIIIIIIIIIIIII4444444444444444444444444444444444")
                    print("Problem infeasible")
                    break     
                else:
                    print("RETORNANDO AQUIIIIIIIIIIIIIIIIIIIIIIIII9999999999999999999999999999999999944")
                    print("matrizB", matrizB)
                    return matrizB,

        #verifica se tem valor negativo 
        for i in range(len(custos)):
            if custos[i] >= maior:     
                maior = custos[i]
                quementranabase = i
        print(custos)
        print("maior =", maior, "custos = ", custos)
        print(custob)

        aux = [0] * len(matrizNB)
        for i in range(len(matrizNB)):
            aux[i] = matrizNB[i][quementranabase]
        y = multiplicamatriz(inversa, aux)
        print("y = ", y)
        
        if all(i <= 0 for i in y):
            print("RETORNANDO AQUIIIIIIIIIIIIIIIIIIIIIIIII5555555555555")
            print("solution unbound")
            return False

        mini = [0] * len(matrizB)
        for i in range(len(y)):
            if(y[i] <= 0):
                mini[i] = 9223372036854775807
            else:
                mini[i] = xb[i]/y[i]
        indice_menor = 0
        for i in range(len(mini)):
            if mini[i] > 0:
                if mini[i] < mini[indice_menor]:
                    indice_menor = i
        print("sai da base = ", indice_menor, ", entra na base = ", quementranabase)
        if all(x <= 0 for x in y):
            print("Solution Unbounded")
        print("custobasico", custob)
        matrizB, matrizNB, custob, custonb, = trocadebase(matrizB, matrizNB, custob, custonb, int(quementranabase), int(indice_menor))
        if all(x == 0 for x in custob):
            print("RETORNANDO AQUIIIIIIIIIIIIIIIIIIIIIIIII3333333333333")
            print("matrizB", matrizB)
            return matrizB
        print("feshow")
        interacao += 1
        
def basicaNaoBasica(objetivo,matrizA):
    custobasico = [i for i in objetivo if i == 0]
    custonaobasico = [i for i in objetivo if i != 0]
    naobasica = [[linha[i] for i in range(len(linha)) if objetivo[i] != 0] for linha in matrizA]
    basica = []
    for j in range(len(objetivo)):
        if objetivo[j] == 0:
            basica.append([matrizA[i][j] for i in range(len(matrizA))])
    return custobasico, custonaobasico, basica, naobasica

def multiplicamatriz(inversa, vetormultiplicador):
    resultado = [0] * len(vetormultiplicador)
    #print("vetormultiplicador ", vetormultiplicador)
    #print("inversa ", inversa)
    for k in range(len(inversa)):
        for i in range(len(vetormultiplicador)):
            aux = inversa[k][i] * vetormultiplicador[i]
            resultado[k] += aux 
    return resultado

def multiplicadorsimplex(inversa, vetormultiplicador):
    resultado = [0] * len(vetormultiplicador)
    for k in range(len(inversa)):
        for i in range(len(inversa[k])):
            aux = inversa[i][k] * vetormultiplicador[i]
            resultado[k] += aux
    return resultado

def custo(naobasicaA, multiplicador, an):
    aux = 0
    for i in range(len(an)):
        aux += an[i] * float(multiplicador[i])   
    return naobasicaA - aux

def trocadebase(matrizB, matrizNB, custobasico, custonaobasico, quementra, quemsai):
    aux1 = [0] * len(matrizNB)
    aux2 = [0] * len(matrizB)
    for i in range(len(matrizNB)):
        aux1[i] = matrizNB[i][quementra]
    for i in range(len(matrizB)):
        aux2[i] = matrizB[i][quemsai]
    for i in range(len(matrizNB)):
        matrizNB[i][quementra] = aux2[i]
    for i in range(len(matrizB)):
        matrizB[i][quemsai] = aux1[i]

    custobasico[quemsai], custonaobasico[quementra] = custonaobasico[quementra], custobasico[quemsai]
    return matrizB, matrizNB, custobasico, custonaobasico

def simplex(custobasico, custonaobasico, matrizB, matrizNB, objetivo, b, num_Variaveis):
    #indices = [i+1 for i in range(len(objetivo))]
    solucaoOtima = 0
    interacao = 0
    xfinal = [0] * num_Variaveis
    quementranabase2 = []
    indice_menor2 = []
    #xb = [0] * len(matrizB)
    while(True | interacao < 10):
        maior = 0
        quementranabase = 0
        inversa = matriz_inversa(matrizB)
        #inversa = np.linalg.inv(matrizB)
        custos = [0] * len(matrizNB)
        quementranabase = 0
        xb = multiplicamatriz(inversa, b)
        multiplicador = multiplicadorsimplex(inversa, custobasico)
        if(len(matrizB) == 1 and len(custonaobasico) > 1):
            aux = [0] * len(matrizNB)
            custos[0] = custo(custonaobasico[0], multiplicador, aux)

        else:
            for i in range(len(custonaobasico)):
                aux = [0] * len(matrizNB)
                for k in range(len(matrizNB)):
                    aux[k] = matrizNB[k][i]
                custos[i] = custo(custonaobasico[i], multiplicador, aux)


        #verifica se tem valor negativo 
        for i in range(len(custos)):      
            if maior > custos[i]:
                maior = custos[i]
                quementranabase = i
        if maior >= 0:
            for i in range(len(custobasico)):
                aux = custobasico[i] * xb[i]
                solucaoOtima += aux
            for i in range(len(quementranabase2)):
                xfinal[quementranabase2[i]] = xb[indice_menor2[i]]
            return solucaoOtima, xfinal
        else:
            aux = [0] * len(matrizNB)
            for i in range(len(matrizNB)):
                aux[i] = matrizNB[i][quementranabase]
            y = multiplicamatriz(inversa, aux)

            mini = [0] * len(matrizB)
            for i in range(len(y)):
                if(y[i] <= 0):
                    mini[i] = 9223372036854775807
                else:
                    mini[i] = xb[i]/y[i]
            indice_menor = 0
            for i in range(len(mini)):
                if mini[i] > 0:
                    if mini[i] < mini[indice_menor]:
                        indice_menor = i
        indice_menor2.append(indice_menor)
        quementranabase2.append(quementranabase)
        if all(x <= 0 for x in y):
            print("Solution Unbounded")
            sys.exit()
        matrizB, matrizNB, custobasico, custonaobasico, = trocadebase(matrizB, matrizNB, custobasico, custonaobasico, int(quementranabase), int(indice_menor))
        interacao += 1
        
      
def main():
    diretorio = 'exemplos'
    arquivos = os.listdir(diretorio)

    while True:
        exercicio_desejado = input("Digite o problema ou clique em (p) para encerrar: \n")
        if(exercicio_desejado == 'p'):
            print("Programa Finalizado ;-(")
            break
        else:
            encontrado = [arquivo for arquivo in arquivos if arquivo.startswith(exercicio_desejado)]
            if encontrado:
                caminho = os.path.join(diretorio, encontrado[0])
                sentido, quantidadeartificiais, sentidoOriginal, objetivo, matrizA, b, num_Variaveis, num_Restricoes = lerArquivoLP(caminho)
                if(quantidadeartificiais > 0):
                    print("precisa artificial")
                    MatrizA = artificial(sentido, objetivo, quantidadeartificiais, matrizA, b, num_Variaveis, num_Restricoes)
                    print("SAIUUUU DA ARTIFICIALLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLL")
                    print(objetivo)
                    print(num_Variaveis)
                    objetivo = objetivo[:-num_Variaveis]
                    print(objetivo)
                    custobasico, custonaobasico, matrizB, matrizNB = basicaNaoBasica(objetivo, MatrizA)
                    solucaoOtima, x =simplex(custobasico, custonaobasico, matrizB, matrizNB, objetivo, b, num_Variaveis)
                else:
                    custobasico, custonaobasico, matrizB, matrizNB = basicaNaoBasica(objetivo, matrizA)
                    solucaoOtima, x =simplex(custobasico, custonaobasico, matrizB, matrizNB, objetivo, b, num_Variaveis)
                    if(sentidoOriginal == "maximize"):
                        solucaoOtima *= -1
                    print("######################################################################################## \n")      
                    print("z: ", solucaoOtima)      
                    k=1
                    for i in range(len(x)):
                        print("x",k,"= ", x[i])
                        k+=1
                    print("\n######################################################################################## \n")
            else:
                print("exercicio não encontrado")
main()

