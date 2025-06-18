const UICard = ({ title, children }) => {
  return (
    <div className="mt-3 border overflow-hidden bg-white" style={{ borderRadius: '3px', marginBottom: '15px' }}>
      <div className="px-3 py-2 border-bottom" style={{ fontSize: '0.95rem', backgroundColor: '#f5f5f5' }}>
        {title}
      </div>
      <div style={{ fontSize: '0.8rem' }}>
        {children}
      </div>
    </div>
  );
};

export default UICard;
