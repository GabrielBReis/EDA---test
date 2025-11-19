import cv2

# tenta abrir a câmera com DirectShow
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

if not cap.isOpened():
    print("Não consegui abrir a câmera :(")
    exit(1)

print("Câmera aberta! Pressione ESC para sair.")

while True:
    ret, frame = cap.read()
    if not ret:
        print("Falha ao ler frame da câmera.")
        break

    cv2.imshow("Teste Camera", frame)

    # ESC para sair
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
