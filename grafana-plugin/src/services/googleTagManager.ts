export const pushConvertion = (message: any) => {
  if (window.dataLayer) {
    window.dataLayer.push(message);
  }
};
