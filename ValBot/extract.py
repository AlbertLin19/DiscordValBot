# Import required packages 
import cv2 
import pytesseract 
import os
import numpy as np
import random
import storage
from difflib import SequenceMatcher

hsl_threshold_hue = [0.0, 180.0]
hsl_threshold_saturation = [0.0, 149.82323232323233]
hsl_threshold_luminance = [169.69424460431657, 255.0]


def extract(img_path):

	data = {} # key is in-game name, value is [team color, avg combat score, K, D, A, econ rating, 
	          # first bloods, plants, defuses]

	pytesseract.pytesseract.tesseract_cmd = os.environ.get('tesseract_path')

	# Read image from which text needs to be extracted 
	img = cv2.imread(img_path) 

	# resize
	target_width = 1300
	scale = float(target_width)/img.shape[1]
	target_height = int(scale*img.shape[0])
	img = cv2.resize(img, (target_width, target_height))

	# Convert the image to HSL and filter and close
	processed = cv2.cvtColor(img, cv2.COLOR_BGR2HLS)
	processed = cv2.inRange(processed, (hsl_threshold_hue[0], hsl_threshold_luminance[0], hsl_threshold_saturation[0]),  (hsl_threshold_hue[1], hsl_threshold_luminance[1], hsl_threshold_saturation[1]))
	kernel = np.ones((1,1),np.uint8)
	processed = cv2.morphologyEx(processed, cv2.MORPH_CLOSE, kernel)

	# Appplying dilation on the threshold image 
	rect_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (22, 10)) 
	dilation = cv2.dilate(processed, rect_kernel, iterations = 1) 

	# Finding contours 
	contours, hierarchy = cv2.findContours(dilation, cv2.RETR_EXTERNAL, 
													cv2.CHAIN_APPROX_NONE) 
	print(f'number of contours found: {len(contours)}')

	# Creating a copy of processed image 
	imTess = processed.copy()      # will send to tesseract
	imRects = img.copy()        # will draw rects on this

	# add player keys
	annotation_color = (255, 255, 255)
	roster = storage.getRoster()  # will compare text to keys to see if it should autocorrect
	for cnt in contours: 
		text_color = (255, 255, 100)
		x, y, w, h = cv2.boundingRect(cnt) 

		# Apply OCR on the cropped image iff text is for player name
		if x/float(imTess.shape[1]) < 0.2:
			# Drawing a rectangle on copied image 
			cv2.rectangle(imRects, (x, y), (x + w, y + h), annotation_color, 1)
		
			# Cropping the text block for giving input to OCR 
			cropped = 255 - imTess[y:y + h, x:x + w]  # invert black and white
			cropped = cv2.resize(cropped, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC) # enlarge
			cropped = cv2.bilateralFilter(cropped,9,75,75) # blur
			text = pytesseract.image_to_string(cropped, config=f"--psm 10")

			# autocorrect text if similar enough to roster
			found = False
			max_sim = 0
			threshold_sim = 0.7
			alt_text = ''
			for name, riotIDs in roster.items():
				for riotID in riotIDs:
					sim = SequenceMatcher(None, text, riotID).ratio()
					if sim > max_sim:
						max_sim = sim
						alt_text = riotID
			if max_sim >= threshold_sim:
				text = alt_text
				found = True


			# need to find team color too for player
			cx, cy, cw, ch = x+w, y, int(0.1*img.shape[1]), h
			color_region = img[cy:cy + ch, cx:cx + cw]
			red = 0
			blue = 0
			color = ''
			# randomly sample pixels
			for i in range(100):
				x_coord = random.randrange(0, color_region.shape[1])
				y_coord = random.randrange(0, color_region.shape[0])
				red += color_region[y_coord, x_coord, 2]
				blue += color_region[y_coord, x_coord, 0]
			
			# adjust the y coord for plotting only if too high
			ploty = y
			if ploty < 0.05*imRects.shape[0]:
				ploty = int(0.05*imRects.shape[0])

			if red > blue:
				color = 'red'
				cv2.putText(imRects, f'red', (cx + w, ploty), cv2.FONT_HERSHEY_SIMPLEX, .4, (100, 100, 255), 1)
			else:
				color = 'blue'
				cv2.putText(imRects, f'blue', (cx + w, ploty), cv2.FONT_HERSHEY_SIMPLEX, .4, (255, 255, 100), 1)
		
			cv2.putText(imRects, f'{text}', (x + w, ploty), cv2.FONT_HERSHEY_SIMPLEX, .4, (150, 255, 150), 1)
			if found:
				cv2.rectangle(imRects, (x, y), (x + w, y + h), (0, 0, 0), 3)
			data[text] = [int(y), color]
	
	print(data)
		
	# Looping through the data identified contours
	widths = {} # key: text lengths, value: avg width to compare with contour widths later
	lengths = {} # key: i, value: text length of ith contour
	i = 0
	for cnt in contours: 
		i += 1
		text_color = (150, 255, 150)
		x, y, w, h = cv2.boundingRect(cnt) 
		if x/float(imTess.shape[1]) >= 0.2: # for stats, only detect as digits
			# Drawing a rectangle on copied image 
			cv2.rectangle(imRects, (x, y), (x + w, y + h), annotation_color, 1)
		
			# Cropping the text block for giving input to OCR 
			cropped = imTess[y:y + h, x:x + w]  
			cropped = cv2.resize(cropped, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC) # enlarge
			kernel = np.ones((2,2),np.uint8)
			cropped = cv2.dilate(cropped,kernel,iterations = 2)
			cropped = cv2.bilateralFilter(cropped,9,75,75) # blur
			cropped = 255 - cropped  # invert black and white
			
			# apply OCR on cropped image
			text = pytesseract.image_to_string(cropped, config=f"--psm 13 -c tessedit_char_whitelist=0123456789")

			# if y is too low, make higher
			ploty = y
			if ploty > 0.9*imRects.shape[0]:
				ploty = int(y - int(h*1.7))

			cv2.putText(imRects, f'{text}', (x, ploty + int(h*1.7)), cv2.FONT_HERSHEY_SIMPLEX, .4, text_color, 1)
		
			# Appending the data into closest player by y-coord
			closest = None
			minYDist = float('inf')
			for player in data:
				if abs(y - data[player][0]) < minYDist:
					minYDist =  abs(y - data[player][0])
					closest = player

			data[closest].extend([x, text])
			if len(text) not in widths:
				widths[len(text)] = (len(text), 1)
			else:
				old_width, num = widths[len(text)]
				widths[len(text)] = (((float(old_width)*num)+w)/(num + 1), num + 1)
			lengths[i-1] = len(text)

	print(widths)
	# recolor if width is closer to wrong avg
	for i in range(len(contours)):
		x, y, w, h = cv2.boundingRect(contours[i]) 

		if x/float(imTess.shape[1]) >= 0.2: # for stats
			avg_width = widths[lengths[i]][0] # avg width for this text length
			other_widths = []
			for length_key in widths:
				if length_key != lengths[i]:
					other_widths.append(widths[length_key][0])
			diff = abs(avg_width - w)
			for other_width in other_widths:
				if abs(other_width - w) < diff:
					cv2.rectangle(imRects, (x, y), (x + w, y + h), (150, 150, 255), 3)

	if len(data) != 10:
		print(f'Number of players found ({len(data)}) does not equal 10! ERROR')
		return [], imRects, f'Number of players found ({len(data)}) does not equal 10! ERROR'

	# reformat the [y, color, x1, stat1, x2, stat2,...] into ordered [color, stat1, stat2, ...]
	for key, value in data.items():
		if len(value) != 18:
			print(f'Data not associated properly for {key}! ERROR')
			return [], imRects, f'Data not associated properly for {key}! ERROR'
		stats = data[key][2:]
		xs = stats[0::2]
		nums = stats[1::2]
		indices = np.argsort(xs)
		newStats = [None] * (len(nums) + 1)
		newStats[0] = data[key][1]
		for i in range(len(nums)):
			newStats[indices[i]+1] = nums[i]
		data[key] = newStats

	print('FINAL DATA:')
	print(data)
	return data, imRects, None
