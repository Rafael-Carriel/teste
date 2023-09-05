import cplex
import np
import sys
import os

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

    necessita_artificiais = False

    for i in range(num_Restricoes):
        lin_expr = cpx.linear_constraints.get_rows(i)
        lin_expr = [(n,m) for n,m in zip(lin_expr.ind,lin_expr.val)]
        for j in lin_expr:
            matrizA[i][j[0]]=j[1]
        
        sentido = cpx.linear_constraints.get_senses(i)
        sen
        #folga
        for x in range(num_Restricoes):
            matrizA[x].append(0)
        matrizA[i][-1]=1
        objetivo.append(0)
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

    #printar o problema já na forma padrão
    print(b)
    print(objetivo)
    print(matrizA)
    print("quantidade de artificiais: ", quantidadeartificiais)

    return sen, quantidadeartificiais, sentidoOriginal, objetivo, matrizA, b, num_Variaveis, num_Restricoes

def artificial(sentido, objetivo, quantidadeartificiais, matrizA, b, num_Variaveis):
    novo_objetivo = [0] * len(objetivo)
    print(sentido)
    for i in range(quantidadeartificiais):
        novo_objetivo.append(1)
    print("novo objetivo = ", novo_objetivo)

        #adiciona as váriaveis artificiais
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
   
    for x in range(num_Variaveis, ((len(matrizA[0]) - quantidadeartificiais) - 1)):
        matrizB.append([matrizA[i][x] for i in range(len(matrizA))])
        custob.append(novo_objetivo[x])
    for x in range(len(novo_objetivo)):
        if novo_objetivo[x] == 1:
            matrizB.append([matrizA[i][x] for i in range(len(matrizA))])
            custob.append(novo_objetivo[x])
    for x in range(num_Variaveis):
        matrizNB.append([matrizA[i][x] for i in range(len(matrizA))])
        custonb.append(novo_objetivo[x])
    for x in range(len(matrizA[0]) - quantidadeartificiais, len(matrizA[0])):
        matrizNB.append([matrizA[i][x] for i in range(len(matrizA))])
        custonb.append(novo_objetivo[x])
    matrizNB = np.transpose(matrizNB)
    print("matriz nao basicas = ", matrizNB)
    print("custonb = ", custonb) 
    print("matriz basicas = ", matrizB)
    print("custob = ", custob)        
    
    interacao = 0
    while(True):
        print("Iteracao = ", interacao, "\n")
        maior = 0
        quementranabase = 0
        #inversa das basicas
        #inversa = matriz_inversa(matrizB)
        inversa = np.linalg.inv(matrizB)
        print("inversa = ", inversa)
        #vetor com os custo
        custos = [0] * len(custonb)
        print("custo = ", custos)
        xb = multiplicamatriz(inversa, b)
        print("xb = ", xb, "\n")
        multiplicador = multiplicadorsimplex(inversa, b)
        print("lambda = ", multiplicador, "\n")

        #chama os calculos
        print("matriz[0] = ", len(matrizNB))
        print("custo nao basico = ", custonb)
        for i in range(len(matrizNB[0])):        
            aux = [0] * len(matrizNB[0])
            for k in range(len(matrizNB[0])):
                aux[k] = matrizNB[k][i]
            print("custo não basico = ", custonb[i], " multiplicador = ", multiplicador, " matriznb = ", aux)
            custos[i] = custo(custonb[i], multiplicador, aux)
            print("custo ", i, " = ", custos[i], "\n")

        #passo 3
        for i in range(len(custos)):      
            if maior > custos[i]:
                maior = custos[i]
                quementranabase = i
        if all(x >= 0 for x in custos):
            print("entrou aqui")
            print("custob =", custob)
            for i in custob:
                if i == 1:
                    print("Problem infeasible")
                    break
                else:
                    return matrizB, matrizNB, custob, custonb
        if maior >= 0:

            return matrizB, matrizNB, custob, custonb
        else:

            aux = [0] * len(matrizNB)
            for i in range(len(matrizNB)):
                aux[i] = matrizNB[i][quementranabase]
            print(inversa, aux)
            y = multiplicamatriz(inversa, aux)
            if all(i <= 0 for i in y):
                return False
            else:
                mini = [0] * len(matrizB)
                for i in range(len(y)):
                    if(y[i] == 0):
                        mini[i] = 9223372036854775807
                    else:
                        mini[i] = xb[i]/y[i]             
                indice_menor = 0
                print("min = ", mini, "\n")
                for i in range(len(mini)):
                    if mini[i] < mini[indice_menor]:
                        indice_menor = i
        print(mini)
        print("sai da base = ", indice_menor, ", entra na base = ", quementranabase)
        
        matrizB, matrizNB, custob, custonb = trocadebase(matrizB, matrizNB, custob, custonb, int(quementranabase), int(indice_menor))
        interacao += 1
        
def matriz_inversa(matriz):
    n = len(matriz)
    identidade = [[float(i == j) for j in range(n)] for i in range(n)]
    for j in range(n):
        for i in range(j + 1, n):
            mult = matriz[i][j] / matriz[j][j]
            for k in range(n):
                matriz[i][k] -= mult * matriz[j][k]
                identidade[i][k] -= mult * identidade[j][k]

    for j in range(n - 1, -1, -1):
        for i in range(j - 1, -1, -1):
            mult = matriz[i][j] / matriz[j][j]
            for k in range(n):
                matriz[i][k] -= mult * matriz[j][k]
                identidade[i][k] -= mult * identidade[j][k]

    for i in range(n):
        div = matriz[i][i]
        for j in range(n):
            matriz[i][j] /= div
            identidade[i][j] /= div

    return identidade
    
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
    indices = [i+1 for i in range(len(objetivo))]
    solucaoOtima = 0
    interacao = 0
    xfinal = [0] * num_Variaveis
    quementranabase2 = []
    indice_menor2 = []
    xb = [0] * len(matrizB)
    while(True):
        maior = 0
        quementranabase = 0
        inversa = np.linalg.inv(matrizB)
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
        # if all(x >= 0 for x in custos):
        #     for i in custobasico:
        #         if i != 0:
        #             print("Problem infeasible")
        #             sys.exit()
        if maior >= 0 & len(custos) > 2:
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

            if all(x <= 0 for x in y) | len(y) < 2:
                print("Solution Unbound")
                sys.exit()

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
        #print("sai da base = ", indice_menor, ", entra na base = ", quementranabase)
        indice_menor2.append(indice_menor)
        quementranabase2.append(quementranabase)
        matrizB, matrizNB, custobasico, custonaobasico, = trocadebase(matrizB, matrizNB, custobasico, custonaobasico, int(quementranabase), int(indice_menor))
        interacao += 1
        
      
def main():
    diretorio = 'exemplos'
    arquivos = os.listdir(diretorio)

    while True:
        exercicio_desejado = input("Digite o problema ou clique em (p) para encerrar: ")
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
                        matrizB, matrizNB, custob, custonb = artificial(sentido, objetivo, quantidadeartificiais, matrizA, b, num_Variaveis)
                        solucaoOtima, x =simplex(custob, custonb, matrizB, matrizNB, objetivo, b, num_Variaveis)
                    else:
                        print("Não precisa de artificial")
                        custobasico, custonaobasico, matrizB, matrizNB = basicaNaoBasica(objetivo, matrizA)
                        solucaoOtima, x = simplex(custobasico, custonaobasico, matrizB, matrizNB, objetivo, b, num_Variaveis)
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

