import math
def magnitude(A):
    total = 0
    for i in range(len(A)):
        total += pow(A[i], 2)
    return math.sqrt(total)

def addition(A, B):
    if len(A) == len(B):
        C = []
        for i in range(len(A)):
            C.append(A[i] + B[i])
        return C
    return False

def subtraction(A, B):
    if len(A) == len(B):
        C = []
        for i in range(len(A)):
            C.append(A[i] - B[i])
        return C
    return False

def scalar(A, multiple):
    B = []
    for i in range(len(A)):
        B.append(A[i] * multiple)
    return B

def dot_product(A, B):
    if len(A) == len(B):
        total = 0
        for i in range(len(A)):
            total += A[i] * B[i]
        return total
    return False

def cross_product(A, B):
    C = []
    C.append(A[1] * B[2] - A[2] * B[1])
    C.append(A[2] * B[0] - A[0] * B[2])
    C.append(A[0] * B[1] - A[1] * B[0])
    return C

def main():
    A = [2, 3, 4]
    B = [1, 5, 2]
    multiple = float(input("Enter the constant you want to multiply by: "))
    print(scalar(A, multiple))
    print(magnitude(A))
    print(addition(A, B))
    print(subtraction(A, B))
    print(dot_product(A, B))
    print(cross_product(A, B))

if __name__ == "__main__":
    main()