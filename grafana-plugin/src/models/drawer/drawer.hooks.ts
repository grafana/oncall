import { useStore } from 'state/useStore';

export const useDrawerData = <T>() => {
  const { drawerStore } = useStore();
  return drawerStore.drawerData as T;
};
