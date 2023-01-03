export default function loadCss(url: string) {
  return new Promise((resolve, _reject) => {
    let link = document.createElement('link');
    link.type = 'text/css';
    link.rel = 'stylesheet';
    link.onload = resolve;
    link.href = url;

    const head = document.getElementsByTagName('head')[0];
    head.appendChild(link);

    return link;
  });
}
