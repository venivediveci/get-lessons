
Param(
    $Path,
    $Url
)

python .\get_lesson.py $Path $Url

aria2c -i .\downloads\$Path\mp4_info.txt -d .\downloads\$Path\