from pathlib import Path

ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parents[1]
SOURCE = WORKSPACE / 'esp32S3/Guitar_Controller'
TARGET = WORKSPACE / 'esp32S3/Guitar_Controller_R15'


def main():
    paths = [Path('CMakeLists.txt'), Path('sdkconfig'), Path('sdkconfig.defaults')]
    paths.extend(path.relative_to(SOURCE) for path in sorted((SOURCE/'main').iterdir()) if path.is_file())
    print('*** Begin Patch')
    for relative in paths:
        destination = TARGET / relative
        if destination.exists():
            raise ValueError(f'Refusing to overwrite {destination}')
        source = (SOURCE/relative).read_text(encoding='utf-8')
        if relative.as_posix() == 'main/fpga_protocol.c':
            source = source.replace('return (c >= 0x02 && c <= 0x06)', 'return (c >= 0x02 && c <= 0x06) || c == 0x08')
        elif relative.as_posix() == 'main/fpga_link.c':
            source = source.replace('== 1 && a <= 2)', '== 1 && a <= 3)').replace('== 2 && a <= 2 && b <= 127)', '== 2 && a <= 3 && b <= 127)')
            anchor = '    } else if (sscanf(line, "FPGA,MODE,%u%c"'
            if source.count(anchor) != 1:
                raise ValueError('Unexpected S3 control parser')
            source = source.replace(anchor, '''    } else if (sscanf(line, "FPGA,VIOLIN,%u,%u,%u%c", &a, &b, &c, &extra) == 3 &&
               a >= 55 && a <= 100 && b >= 1 && b <= 127 && (c == 0 || c == 1 || c == 3)) {
        ok = enqueue(0x08, a, b, c);
    } else if (sscanf(line, "FPGA,MODE,%u%c"''')
        elif relative.as_posix() == 'CMakeLists.txt':
            source = source.replace('project(Guitar_Controller_S3)', 'project(Guitar_Controller_S3_R15)')
        print('*** Add File: '+str(destination).replace('\\','/'))
        print('\n'.join('+'+line for line in source.splitlines()))
    print('*** End Patch')


if __name__ == '__main__':
    main()
