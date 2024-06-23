import sys
import re
import glob

def transfer_mark(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        content = file.read()

    # Use regular expressions to find and replace ==text== with <mark>text</mark>
    new_content = re.sub(r'==(.*?)==', r'<mark>\1</mark>', content)
    # 将$ text $ 替换为 $text$ 避免前后出现的空格导致公式无法正常显示
    # 暂时还不能处理如text$$LaTeX$$text, LaTeX中有换行符的情况
    # 但是这种不应该出现, 手动修复吧
    new_content = re.sub(r'\$?\$\ ?(.*?)\ ?\$\$?', r'$\1$', new_content)
    # plan1: 在`$$\n\n$$`之间再加一个换行符 
    new_content = re.sub(r'\$\$\n\n\$\$', r'$$\n\n\n$$', new_content)
    
     # 在文字和换行后的$$之间再加一个换行符
    new_content = re.sub(r'(\n\n?)(\$\$([\s\S]*?)\$\$)(\n\n?)', r'\n\n\2\n\n', new_content)
    
    # 将$$段内部的连续换行符替换为一个换行符
    new_content = re.sub(r'(\n\n\$\$)([\s\S]*?)(\$\$\n\n)', lambda x: x.group(1) + re.sub(r'\n+', r'\n', x.group(2)) + x.group(3), new_content)
    
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(new_content)
    
    print(f'Transferred file: {filename}')

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: python transfer_mark.py <filename>')
        sys.exit(1)

    filenames = glob.glob(sys.argv[1])
    for filename in filenames:
        transfer_mark(filename)