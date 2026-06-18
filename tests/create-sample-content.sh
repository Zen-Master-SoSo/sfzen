IFS=$(echo -en "\n\b")
for f in $(find . -name \*.wav)
do
	echo "$f" > "$f"
done
