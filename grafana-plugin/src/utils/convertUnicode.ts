export default function convertUnicode(input) {
  return input.replace(/\\+u([0-9a-fA-F]{4})/g, (_a, b) => String.fromCharCode(parseInt(b, 16)));
}
