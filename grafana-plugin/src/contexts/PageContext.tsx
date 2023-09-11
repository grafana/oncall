import { createContext } from 'react';

interface PageContextInterface {
  pageTitle: string;
  setPageTitle?: (title: string) => void;
}

export const PageContext = createContext<PageContextInterface>({ pageTitle: '' });
