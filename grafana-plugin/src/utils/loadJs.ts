export default function loadJs(url: string) {
  let script = document.createElement('script');
  script.src = url;

  document.head.appendChild(script);
}
