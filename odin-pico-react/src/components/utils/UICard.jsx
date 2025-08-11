const UICard = ({ title, children, headerContent }) => {
  return (
    <div className="mt-3 border overflow-hidden" style={{ borderRadius: '3px', marginBottom: '15px' }}>
      <div className="px-3 py-2 border-bottom" style={{ fontSize: '0.95rem', backgroundColor: '#f5f5f5' }}>
        {headerContent || title}
      </div>
      <div>
        {children}
      </div>
    </div>
  );
};

export default UICard;
