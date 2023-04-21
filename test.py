# from googletrans import Translator
# eng = "hello"
# reply = Translator().translate(eng, dest='vi').text

# print(reply)
import pytesseract
import cv2

img = cv2.imread("test.png")
text = pytesseract.image_to_string(img, lang="eng")
print(text)