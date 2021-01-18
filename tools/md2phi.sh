#!/bin/sh

PHI_PATH="/Users/brunoc/Dropbox/Fichas/Φ"

BASE_FN=`basename "${1}" | sed 's/\.md$//'`
PHI_ID=`echo "${BASE_FN}" | awk '{ print $1 }'`
EXPAND_FN=$(echo "${PHI_PATH}/${PHI_ID} "*".markdown")
NEW_FN="${PHI_PATH}/${BASE_FN}.markdown"
TRASH_PATH="/Users/brunoc/.Trash"

if [ -f "${EXPAND_FN}" ] && [ "${NEW_FN}" != "${EXPAND_FN}" ] || [ `ls -1 "${PHI_PATH}/${PHI_ID} "*".markdown" 2>/dev/null | wc -l ` -gt 1 ]; then
	STATUS=`osascript -so <<EOF
display dialog "Ok to move duplicates to trash? ${EXPAND_FN}" with icon caution
EOF
`
	[ "${STATUS}" != "button returned:OK" ] && echo "Cancelled by user" >&2 && exit 1
	mv -f "${PHI_PATH}/${PHI_ID} "*".markdown" "${TRASH_PATH}"
fi

/Users/brunoc/GitHub/zettel-composer/tools/md2phi.py "${PHI_PATH}" "${1}"