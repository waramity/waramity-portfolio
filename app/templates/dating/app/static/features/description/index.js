function addLinks(str) {
  const regex = /(https?:\/\/[^\s]+)/g;
  return str.replace(regex, '<a href="$1">$1</a>');
}

function addLineBreaks(str) {
  return str.replace(/\n/g, "<br>");
}

function prepareDescription(str) {
  str = addLinks(str);
  str = addLineBreaks(str);
  return str;
}
