# Import required packages 
import cv2 
import pytesseract 
import os

hsl_threshold_hue = [0.0, 180.0]
hsl_threshold_saturation = [0.0, 149.82323232323233]
hsl_threshold_luminance = [169.69424460431657, 255.0]


def extract(img_path):

	data = {}
	pytesseract.pytesseract.tesseract_cmd = os.environ.get('tesseract_path')

	# Read image from which text needs to be extracted 
	img = cv2.imread(img_path) 

	# Preprocessing the image starts 

	# Convert the image to HSL and filter
	hsl = cv2.cvtColor(img, cv2.COLOR_BGR2HLS)
	hsl = cv2.inRange(hsl, (hsl_threshold_hue[0], hsl_threshold_luminance[0], hsl_threshold_saturation[0]),  (hsl_threshold_hue[1], hsl_threshold_luminance[1], hsl_threshold_saturation[1]))
	cv2.imshow('hsl filter', hsl)
	cv2.waitKey(0)
	cv2.destroyAllWindows()

	# Performing OTSU threshold 
	# ret, thresh1 = cv2.threshold(hsl, 0, 255, cv2.THRESH_OTSU | cv2.THRESH_BINARY_INV) 

	# Specify structure shape and kernel size. 
	# Kernel size increases or decreases the area 
	# of the rectangle to be detected. 
	# A smaller value like (10, 10) will detect 
	# each word instead of a sentence. 
	rect_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (20, 10)) 

	# Appplying dilation on the threshold image 
	dilation = cv2.dilate(hsl, rect_kernel, iterations = 1) 
	cv2.imshow('dilated', dilation)
	cv2.waitKey(0)
	cv2.destroyAllWindows()

	# Finding contours 
	contours, hierarchy = cv2.findContours(dilation, cv2.RETR_EXTERNAL, 
													cv2.CHAIN_APPROX_NONE) 
	print(f'number of contours found: {len(contours)}')
	for cnt in contours:
		print(f'{cv2.boundingRect(cnt) }')

	# Creating a copy of hsl image 
	im2 = hsl.copy() 
	imRects = hsl.copy()  # will draw rects on this

	# Looping through the identified contours 
	# Then rectangular part is cropped and passed on 
	# to pytesseract for extracting text from it 
	# Extracted text is then written into the text file 
	annotation_color = (240, 255, 246)
	i = 0
	for cnt in contours: 
		x, y, w, h = cv2.boundingRect(cnt) 
		
		# Drawing a rectangle on copied image 
		cv2.rectangle(imRects, (x, y), (x + w, y + h), annotation_color, 3)
		
		# Cropping the text block for giving input to OCR 
		cropped = im2[y:y + h, x:x + w]
		
		# Apply OCR on the cropped image 
		text = pytesseract.image_to_string(cropped) 

		cv2.putText(imRects, f'{i}. {text}', (x + h, y + h), cv2.FONT_HERSHEY_SIMPLEX, .5, annotation_color, 1.2)
		
		# Appending the text into file 
		data[i] = text
		i+=1
	cv2.imshow('detected text', imRects)
	cv2.waitKey(0)
	cv2.destroyAllWindows()
	return data
