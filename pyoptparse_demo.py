from optparse import OptionParser

opt_parser = OptionParser()

opt_parser.add_option('-f', '--file', action='store', type='string', dest='filename')
opt_parser.add_option('-v', '--version', action='store_true', dest='verbose', default="hello", help='make lots of noise [default]')

# opt_parser.parse_args() 剖析并返回一个字典和列表
# 字典中的关键字是我们的所有的add_option()函数中的dest参数值
# 而对应的value值，是add_option()函数中的default值或由用户传入的参数值

# store 表示命令行参数的值保存到options对象中
# store_false 若存在'-v'将返回False，而不是 '-v' 后面的参数值，即该选项只与 '-v' 是否存在有关，有则返回False，没有则返回 default对应的值
# store_true 有'-v'则返回True，没有则返回 default值，若没有default则为None

# 例如：
"""
### store_false时
# 无 -v 时，返回 default 值
>python pyoptparse_demo.py -f abc.txt 123 xx
option: {'filename': 'abc.txt', 'verbose': 'hello'}
args: ['123', 'xx']

# 有 -v 时，返回 False
>python pyoptparse_demo.py -f abc.txt -v 123 xx
option: {'verbose': False, 'filename': 'abc.txt'}
args: ['123', 'xx']


### store_true时
>python pyoptparse_demo.py -f abc.txt 123 xx
option: {'filename': 'abc.txt', 'verbose': 'hello'}
args: ['123', 'xx']

>python pyoptparse_demo.py -f abc.txt -v 123 xx
option: {'verbose': True, 'filename': 'abc.txt'}
args: ['123', 'xx']
"""

if __name__ == "__main__":
    option, args = opt_parser.parse_args()
    print("option:", option)
    print("args:", args)

