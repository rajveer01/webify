from django.shortcuts import render
from django.http import HttpResponse
from . import remote_file_selector
import os
# Create your views here.


def home(request):
    return render(request, 'plab_utilities/home.html')


def about(request):
    ip = '10.81.1.107'
    # ip = '127.0.0.1'
    selected = request.GET.get('selected', r'//{ip}'.format(ip=ip))
    print(selected)
    root, dir_of_selected = remote_file_selector.get_dir_list(selected, ip)
    x = root
    print(x)
    paths = [x]
    while True:
        x = os.path.dirname(x)
        if x not in paths:
            paths.insert(0, x)
        else:
            break

    paths.insert(0, x.rstrip('/').rsplit('/', 1)[0])
    paths = [path.replace('\\', '/').rstrip('/') for path in paths]
    print(paths)
    while '' in paths:
        paths.remove('')
    print(paths)
    context = {'options': dir_of_selected, 'directory': paths}

    return render(request, 'plab_utilities/about.html', context=context)


def browse(request):
    return 'some'

def test(request):
    x = render(request, 'plab_utilities/home.html')
    print(x)
    print(type(x))
    print(str(x))
    return HttpResponse('raj')




