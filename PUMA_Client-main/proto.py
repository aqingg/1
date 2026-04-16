from grpc_tools import protoc
import os

def compile_all_protos(proto_dir=".", output_dir="."):
    """
    编译指定目录下的所有 .proto 文件。
    
    :param proto_dir: 包含 .proto 文件的源目录。
    :param output_dir: 生成的 Python 文件的输出目录。
    """
    print(f"正在编译 '{proto_dir}' 目录下的 .proto 文件...")
    
    # 确保输出目录存在
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    proto_files = [f for f in os.listdir(proto_dir) if f.endswith('.proto')]
    if not proto_files:
        print("没有找到 .proto 文件。")
        return

    for proto_file in proto_files:
        command = [
            '',  # 留空，对应 sys.argv[0]
            f'--proto_path={proto_dir}',
            f'--python_out={output_dir}',
            os.path.join(proto_dir, proto_file)
        ]
        
        print(f"正在运行命令: protoc {' '.join(command[1:])}")
        
        # 调用 protoc.main
        result = protoc.main(command)
        
        if result != 0:
            print(f"编译文件 '{proto_file}' 失败，错误码: {result}")
        else:
            print(f"成功编译 '{proto_file}'")

if __name__ == '__main__':
    # 将编译后的文件也输出到当前目录
    compile_all_protos(proto_dir=".", output_dir=".")