import zipfile
from io import BytesIO


def create_zip(files_data_map):
	'''create a zip file in memery and return it

		files_data_map: dict object mapping file name to contents
	    >>> files_data_map = {'a.txt': b'Content of a.txt',
         'b.txt': b'Content of b.txt',
         'c.txt': b'Content of c.txt'}

	'''

	# Create an in-memory buffer
	memory_buffer = BytesIO()

	# Create a ZipFile object that writes to the in-memory buffer
	with zipfile.ZipFile(memory_buffer, 'w') as zip_file:
	    for filename, content in files_data_map.items():
	        zip_file.writestr(filename, content)

	# Get the contents of the in-memory buffer
	zip_data = memory_buffer.getvalue()
	
	return zip_data


if __name__ == '__main__':
	data = main()