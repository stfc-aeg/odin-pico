const UICard = ({ title, children }) => {
  return (
    <div className="mt-3 border overflow-hidden bg-white" style={{ borderRadius: '3px' }}>
      <div className="bg-light px-3 py-2 border-bottom" style={{ fontSize: '0.95rem' }}>
        {title}
      </div>
      <div className="p-2 fw-bold" style={{ fontSize: '0.8rem' }}>
        {children}
      </div>
    </div>
  );
};

export default UICard;
