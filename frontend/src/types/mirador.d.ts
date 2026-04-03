declare module 'mirador';

declare module 'mirador/dist/cjs/src/plugins/OSDReferences' {
  interface OpenSeadragonViewerRef {
    viewport?: {
      goHome?: (immediately?: boolean) => void;
    };
  }

  export const OSDReferences: {
    get(windowId: string): { current?: OpenSeadragonViewerRef } | undefined;
    set(windowId: string, ref: { current?: OpenSeadragonViewerRef }): void;
    refs: Record<string, { current?: OpenSeadragonViewerRef }>;
  };
}
