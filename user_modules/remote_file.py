import os

from walkabout.helpers.moduleslib import networked_function


logfile = None


@networked_function(buffered=False)
def save_file(filename):
    global logfile
    if r'/' in filename:
        path = filename.split('/')
    elif r'\\' in filename:
        path = filename.split('\\')
    else:
        path = [filename]

    current_dir = []
    for directory in path[:-1]:
        current_dir.append(directory)
        if not os.path.exists(''.join(current_dir)):
            print('fo')
            os.mkdir(''.join(os.path.join(current_dir)))
    logfile = open(filename, 'w')


@networked_function(buffered=True)
def write(event):
    global logfile
    print(event)
    logfile.write(event)
    logfile.flush()


@networked_function(buffered=False)
def test_me():
    print('test')