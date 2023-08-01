/**
 * Will append a new JS script
 * @param  {string} url of the script
 * @param  {string} id optional id. If specified, the script will be loaded only once for that given id
 */
export default function loadJs(url: string, id: string = undefined) {
  if (id) {
    const existingScript = document.getElementById(url);
    if (existingScript) {
      return;
    }
  }

  let script = document.createElement('script');
  script.src = url;

  if (id) {
    // optional
    script.id = id;
  }

  document.head.appendChild(script);
}
