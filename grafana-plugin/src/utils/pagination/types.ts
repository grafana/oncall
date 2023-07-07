export type BasePaginatedApiResponse<R extends Record<string, any>> = {
  next: string;
  previous: string;
  results: R[];
  page_size: number;
};

export type CursorPaginatedApiResponse<R> = BasePaginatedApiResponse<R>;

export interface PageNumberPaginatedApiResponse<R> extends BasePaginatedApiResponse<R> {
  count: number;
  current_page_number: number;
  total_pages: number;
}

export type PageNumberPaginatedResultIds = PageNumberPaginatedApiResponse<string>;

export type TablePaginationProps<RT> = Omit<PageNumberPaginatedApiResponse<RT>, 'results'> & {
  onChange: (page: number) => void;
};
