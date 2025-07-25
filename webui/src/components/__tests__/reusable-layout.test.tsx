import { render, screen } from '@testing-library/react';
import {
  PageLayout,
  CardLayout,
  SectionLayout,
  GridLayout,
  FlexLayout,
  StatusCard,
  LoadingContainer,
  EmptyState,
} from '../ui/reusable-layout';

describe('Reusable Layout Components', () => {
  describe('PageLayout', () => {
    it('renders with children', () => {
      render(
        <PageLayout>
          <div data-testid='page-content'>Page Content</div>
        </PageLayout>
      );

      expect(screen.getByTestId('page-content')).toBeInTheDocument();
    });

    it('applies correct styling', () => {
      render(
        <PageLayout>
          <div>Content</div>
        </PageLayout>
      );

      const container = screen.getByText('Content').closest('div');
      expect(container?.parentElement?.parentElement).toHaveClass('min-h-screen', 'bg-gray-50');
    });

    it('applies custom className', () => {
      render(
        <PageLayout className='custom-page'>
          <div>Content</div>
        </PageLayout>
      );

      const container = screen.getByText('Content').closest('div');
      expect(container?.parentElement?.parentElement).toHaveClass('custom-page');
    });
  });

  describe('CardLayout', () => {
    it('renders with children', () => {
      render(
        <CardLayout>
          <div data-testid='card-content'>Card Content</div>
        </CardLayout>
      );

      expect(screen.getByTestId('card-content')).toBeInTheDocument();
    });

    it('applies correct styling', () => {
      render(
        <CardLayout>
          <div>Content</div>
        </CardLayout>
      );

      const card = screen.getByText('Content').parentElement;
      expect(card).toHaveClass(
        'bg-white',
        'rounded-lg',
        'border',
        'border-gray-200',
        'shadow-sm',
        'p-6'
      );
    });

    it('applies different padding sizes', () => {
      const { rerender } = render(
        <CardLayout padding='sm'>
          <div>Content</div>
        </CardLayout>
      );

      let card = screen.getByText('Content').parentElement;
      expect(card).toHaveClass('p-4');

      rerender(
        <CardLayout padding='lg'>
          <div>Content</div>
        </CardLayout>
      );

      card = screen.getByText('Content').parentElement;
      expect(card).toHaveClass('p-8');
    });

    it('applies custom className', () => {
      render(
        <CardLayout className='custom-card'>
          <div>Content</div>
        </CardLayout>
      );

      const card = screen.getByText('Content').parentElement;
      expect(card).toHaveClass('custom-card');
    });
  });

  describe('SectionLayout', () => {
    it('renders with title and children', () => {
      render(
        <SectionLayout title='Section Title'>
          <div data-testid='section-content'>Section Content</div>
        </SectionLayout>
      );

      expect(screen.getByText('Section Title')).toBeInTheDocument();
      expect(screen.getByTestId('section-content')).toBeInTheDocument();
    });

    it('renders with subtitle', () => {
      render(
        <SectionLayout title='Title' subtitle='Subtitle'>
          <div>Content</div>
        </SectionLayout>
      );

      expect(screen.getByText('Subtitle')).toBeInTheDocument();
    });

    it('renders without title', () => {
      render(
        <SectionLayout>
          <div data-testid='content'>Content</div>
        </SectionLayout>
      );

      expect(screen.getByTestId('content')).toBeInTheDocument();
    });

    it('applies custom className', () => {
      render(
        <SectionLayout title='Title' className='custom-section'>
          <div>Content</div>
        </SectionLayout>
      );

      const section = screen.getByText('Title').closest('section');
      expect(section).toHaveClass('custom-section');
    });
  });

  describe('GridLayout', () => {
    it('renders with children', () => {
      render(
        <GridLayout>
          <div data-testid='grid-item-1'>Item 1</div>
          <div data-testid='grid-item-2'>Item 2</div>
        </GridLayout>
      );

      expect(screen.getByTestId('grid-item-1')).toBeInTheDocument();
      expect(screen.getByTestId('grid-item-2')).toBeInTheDocument();
    });

    it('applies different column configurations', () => {
      const { rerender } = render(
        <GridLayout cols={2}>
          <div>Item 1</div>
          <div>Item 2</div>
        </GridLayout>
      );

      let grid = screen.getByText('Item 1').parentElement;
      expect(grid).toHaveClass('grid', 'grid-cols-1', 'md:grid-cols-2', 'gap-4');

      rerender(
        <GridLayout cols={4}>
          <div>Item 1</div>
          <div>Item 2</div>
        </GridLayout>
      );

      grid = screen.getByText('Item 1').parentElement;
      expect(grid).toHaveClass('grid', 'grid-cols-1', 'md:grid-cols-2', 'lg:grid-cols-4', 'gap-4');
    });

    it('applies different gap sizes', () => {
      const { rerender } = render(
        <GridLayout gap='sm'>
          <div>Item 1</div>
          <div>Item 2</div>
        </GridLayout>
      );

      let grid = screen.getByText('Item 1').parentElement;
      expect(grid).toHaveClass('gap-3');

      rerender(
        <GridLayout gap='lg'>
          <div>Item 1</div>
          <div>Item 2</div>
        </GridLayout>
      );

      grid = screen.getByText('Item 1').parentElement;
      expect(grid).toHaveClass('gap-6');
    });
  });

  describe('FlexLayout', () => {
    it('renders with children', () => {
      render(
        <FlexLayout>
          <div data-testid='flex-item-1'>Item 1</div>
          <div data-testid='flex-item-2'>Item 2</div>
        </FlexLayout>
      );

      expect(screen.getByTestId('flex-item-1')).toBeInTheDocument();
      expect(screen.getByTestId('flex-item-2')).toBeInTheDocument();
    });

    it('applies different directions', () => {
      const { rerender } = render(
        <FlexLayout direction='row'>
          <div>Item 1</div>
          <div>Item 2</div>
        </FlexLayout>
      );

      let flex = screen.getByText('Item 1').parentElement;
      expect(flex).toHaveClass('flex', 'flex-row', 'justify-start', 'items-start', 'gap-4');

      rerender(
        <FlexLayout direction='col'>
          <div>Item 1</div>
          <div>Item 2</div>
        </FlexLayout>
      );

      flex = screen.getByText('Item 1').parentElement;
      expect(flex).toHaveClass('flex', 'flex-col', 'justify-start', 'items-start', 'gap-4');
    });

    it('applies different justify alignments', () => {
      const { rerender } = render(
        <FlexLayout justify='center'>
          <div>Item 1</div>
          <div>Item 2</div>
        </FlexLayout>
      );

      let flex = screen.getByText('Item 1').parentElement;
      expect(flex).toHaveClass('justify-center');

      rerender(
        <FlexLayout justify='between'>
          <div>Item 1</div>
          <div>Item 2</div>
        </FlexLayout>
      );

      flex = screen.getByText('Item 1').parentElement;
      expect(flex).toHaveClass('justify-between');
    });

    it('applies different align alignments', () => {
      const { rerender } = render(
        <FlexLayout align='center'>
          <div>Item 1</div>
          <div>Item 2</div>
        </FlexLayout>
      );

      let flex = screen.getByText('Item 1').parentElement;
      expect(flex).toHaveClass('items-center');

      rerender(
        <FlexLayout align='end'>
          <div>Item 1</div>
          <div>Item 2</div>
        </FlexLayout>
      );

      flex = screen.getByText('Item 1').parentElement;
      expect(flex).toHaveClass('items-end');
    });
  });

  describe('StatusCard', () => {
    it('renders with title and value', () => {
      render(<StatusCard title='Total Users' value='1,234' />);

      expect(screen.getByText('Total Users')).toBeInTheDocument();
      expect(screen.getByText('1,234')).toBeInTheDocument();
    });

    it('applies different status styles', () => {
      const { rerender } = render(<StatusCard title='Success' value='100' status='success' />);

      let card = screen.getByText('Success').closest('div');
      expect(card?.parentElement?.parentElement).toHaveClass('border-green-500', 'bg-green-50');

      rerender(<StatusCard title='Warning' value='50' status='warning' />);

      card = screen.getByText('Warning').closest('div');
      expect(card?.parentElement?.parentElement).toHaveClass('border-yellow-500', 'bg-yellow-50');

      rerender(<StatusCard title='Error' value='0' status='error' />);

      card = screen.getByText('Error').closest('div');
      expect(card?.parentElement?.parentElement).toHaveClass('border-red-500', 'bg-red-50');
    });

    it('applies custom className', () => {
      render(<StatusCard title='Test' value='100' className='custom-status' />);

      const card = screen.getByText('Test').closest('div');
      expect(card?.parentElement?.parentElement).toHaveClass('custom-status');
    });
  });

  describe('LoadingContainer', () => {
    it('shows loading state when loading is true', () => {
      render(
        <LoadingContainer loading={true} message='Loading data...'>
          <div>Content</div>
        </LoadingContainer>
      );

      expect(screen.getByText('Loading data...')).toBeInTheDocument();
      expect(screen.queryByText('Content')).not.toBeInTheDocument();
    });

    it('shows children when loading is false', () => {
      render(
        <LoadingContainer loading={false} message='Loading data...'>
          <div data-testid='content'>Content</div>
        </LoadingContainer>
      );

      expect(screen.getByTestId('content')).toBeInTheDocument();
      expect(screen.queryByText('Loading data...')).not.toBeInTheDocument();
    });

    it('shows default loading message', () => {
      render(
        <LoadingContainer loading={true}>
          <div>Content</div>
        </LoadingContainer>
      );

      expect(screen.getByText('Loading...')).toBeInTheDocument();
    });

    it('applies custom className', () => {
      render(
        <LoadingContainer loading={true} className='custom-loading'>
          <div>Content</div>
        </LoadingContainer>
      );

      const container = screen.getByText('Loading...').closest('div');
      expect(container?.parentElement).toHaveClass('custom-loading');
    });
  });

  describe('EmptyState', () => {
    it('renders with title', () => {
      render(<EmptyState title='No data found' />);

      expect(screen.getByText('No data found')).toBeInTheDocument();
    });

    it('renders with description', () => {
      render(<EmptyState title='No data' description='Try refreshing the page' />);

      expect(screen.getByText('Try refreshing the page')).toBeInTheDocument();
    });

    it('renders with icon', () => {
      render(<EmptyState title='No data' icon='📭' />);

      expect(screen.getByText('📭')).toBeInTheDocument();
    });

    it('renders with action', () => {
      render(<EmptyState title='No data' action={<button>Refresh</button>} />);

      expect(screen.getByText('Refresh')).toBeInTheDocument();
    });

    it('applies custom className', () => {
      render(<EmptyState title='No data' className='custom-empty' />);

      const container = screen.getByText('No data').closest('div');
      expect(container).toHaveClass('custom-empty');
    });
  });

  describe('Responsive Design', () => {
    it('GridLayout applies responsive classes', () => {
      render(
        <GridLayout cols={3}>
          <div>Item 1</div>
          <div>Item 2</div>
          <div>Item 3</div>
        </GridLayout>
      );

      const grid = screen.getByText('Item 1').parentElement;
      expect(grid).toHaveClass('grid', 'grid-cols-1', 'md:grid-cols-2', 'lg:grid-cols-3', 'gap-4');
    });

    it('PageLayout applies responsive container', () => {
      render(
        <PageLayout>
          <div>Content</div>
        </PageLayout>
      );

      const container = screen.getByText('Content').closest('div');
      expect(container?.parentElement).toHaveClass('max-w-6xl', 'mx-auto');
    });
  });

  describe('Accessibility', () => {
    it('SectionLayout uses semantic HTML', () => {
      render(
        <SectionLayout title='Section'>
          <div>Content</div>
        </SectionLayout>
      );

      const section = screen.getByText('Section').closest('section');
      expect(section).toBeInTheDocument();
    });

    it('StatusCard has proper contrast', () => {
      render(<StatusCard title='Success' value='100' status='success' />);

      const value = screen.getByText('100');
      expect(value).toHaveClass('text-green-700');
    });
  });
});
