import { Component, type ReactNode } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export default class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error('Unhandled error caught by ErrorBoundary:', error, info);
  }

  private handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh', padding: 48 }}>
          <div style={{ textAlign: 'center', maxWidth: 480 }}>
            <h1 style={{ fontSize: 48, marginBottom: 8 }}>500</h1>
            <h2 style={{ marginBottom: 16 }}>页面出错了</h2>
            <p style={{ color: '#666', marginBottom: 24 }}>
              {this.state.error?.message || '发生了未知错误，请刷新页面重试。'}
            </p>
            <button
              type="button"
              onClick={this.handleReload}
              style={{ padding: '8px 24px', fontSize: 16, cursor: 'pointer' }}
            >
              刷新页面
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
