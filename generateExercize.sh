#!bin/sh


cat sudokuAns.py | grep -v \#ANS | grep -v \#HINT > sudokuExNoHint.py
echo "sudokuExNoHint.py created from sudokuAns.py"

cat sudokuAns.py | grep -v \#ANS > sudokuEx.py
echo "sudokuEx.py created from sudokuAns.py"
