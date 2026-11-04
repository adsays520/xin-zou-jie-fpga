param([string]$Python = 'python')
$ErrorActionPreference = 'Stop'
& $Python -m PyInstaller --noconfirm --onedir --windowed --name FPGA_ESP_Control --hidden-import argparse --hidden-import binascii --hidden-import bisect --hidden-import copy --hidden-import csv --hidden-import dataclasses --hidden-import functools --hidden-import hashlib --hidden-import math --hidden-import random --hidden-import re --hidden-import struct --hidden-import threading --hidden-import time --hidden-import types --hidden-import uuid --hidden-import queue --hidden-import wave --hidden-import ast --hidden-import zlib --hidden-import base64 --hidden-import webbrowser --distpath "$PSScriptRoot/dist" --workpath "$PSScriptRoot/build" --specpath "$PSScriptRoot/build" "$PSScriptRoot/launcher.py"
if ($LASTEXITCODE) { throw 'Desktop build failed' }
Write-Host 'Copy EXE and _internal from dist/FPGA_ESP_Control beside launcher.py, keeping application source and resources.'
