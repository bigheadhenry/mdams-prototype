declare namespace JSX {
  interface IntrinsicElements {
    'model-viewer': React.DetailedHTMLProps<React.HTMLAttributes<HTMLElement>, HTMLElement> & {
      src?: string;
      alt?: string;
      ar?: boolean | string;
      'camera-controls'?: boolean | string;
      'auto-rotate'?: boolean | string;
      'interaction-prompt'?: string;
      'shadow-intensity'?: string | number;
      exposure?: string | number;
      'environment-image'?: string;
      poster?: string;
      loading?: string;
    };
  }
}
