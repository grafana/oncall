export function setItem(key: string, value: any) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch (e) {
    console.warn('Local Storage is not available');
  }
}

export function getItem(key: string) {
  try {
    const raw = localStorage.getItem(key);
    if (raw) {
      return JSON.parse(raw);
    }
  } catch (e) {
    console.warn('Local Storage is not available');
  }
}

export function removeItem(key: string) {
  try {
    localStorage.removeItem(key);
  } catch (e) {
    console.warn('Local Storage is not available');
  }
}

export function setLocalStorageItemWithTTL(key: string, value: any, ttl: number) {
  const now = new Date();

  const item = {
    value,
    expiry: now.getTime() + ttl,
  };
  try {
    localStorage.setItem(key, JSON.stringify(item));
  } catch (e) {
    console.warn('Local Storage is not available');
  }
}

export function getLocalStorageItemWithTTL(key: string) {
  let itemStr;
  try {
    itemStr = localStorage.getItem(key);
  } catch (e) {
    console.warn('Local Storage is not available');
    return true;
  }
  if (!itemStr) {
    return false;
  }
  const item = JSON.parse(itemStr);
  const now = new Date();
  if (now.getTime() > item.expiry) {
    localStorage.removeItem(key);
    return false;
  }
  return item.value;
}
