export function pushConvertion(message: any) {
  if (window.dataLayer) {
    window.dataLayer.push(message);
  }
}
