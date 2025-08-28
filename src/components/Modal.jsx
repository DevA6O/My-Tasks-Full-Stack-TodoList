import React from "react";

export default function Modal({ isOpen, onClose, children, classname = "" }) {
    if (!isOpen) return null;

    return (
        <div data-testid="Modal">
            {/* Transparent blackground */}
            <div className="fixed inset-0 bg-black/80 z-50" onClick={onClose}>
                {/* Modal box */}
                <div className="fixed inset-0 flex items-center justify-center z-50">
                    <div 
                        className={`bg-white p-5 rounded shadow-md w-full ${classname}`}
                        onClick={(e) => e.stopPropagation()}>
                        
                        {children}
                    </div>
                </div>
            </div>
        </div>
    )
};