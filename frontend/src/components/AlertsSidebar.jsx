import React from 'react';

function AlertsSidebar({ alerts, onSelectPlate }) {
  return (
    <aside className="sentinel-alerts">

      {/* HEADER */}
      <div className="sentinel-alerts-header">

        <div className="sentinel-alerts-title-row">
          <div>
            <div className="sentinel-section-label">
              THREAT MONITOR
            </div>

            <h3 className="sentinel-alerts-title">
              CROSS-DEPARTMENT ALERTS
            </h3>
          </div>

          <div className="sentinel-alert-count">
            {alerts.length.toString().padStart(2, '0')}
          </div>
        </div>

        <div className="sentinel-alerts-status">
          <span className="sentinel-alert-live-dot" />
          LIVE INTELLIGENCE STREAM
        </div>

      </div>


      {/* ALERT LIST */}
      <div className="sentinel-alerts-list">

        {alerts.length === 0 ? (

          <div className="sentinel-no-alerts">
            <div className="sentinel-no-alerts-line" />

            <div className="sentinel-no-alerts-title">
              NO ACTIVE ALERTS
            </div>

            <div className="sentinel-no-alerts-subtitle">
              SURVEILLANCE NETWORK CLEAR
            </div>
          </div>

        ) : (

          alerts.map(alert => (

            <button
              key={alert.id}
              type="button"
              className="sentinel-alert-card"
              onClick={() =>
                onSelectPlate &&
                onSelectPlate(alert.plate_number)
              }
            >

              {/* ALERT INDICATOR */}
              <div className="sentinel-alert-indicator" />

              <div className="sentinel-alert-content">

                {/* TIME */}
                <div className="sentinel-alert-time">
                  {alert.timestamp}
                </div>


                {/* PLATE + ACTION */}
                <div className="sentinel-alert-main-row">

                  <span className="sentinel-alert-plate">
                    {alert.plate_number}
                  </span>

                  <span className="sentinel-alert-action">
                    INVESTIGATE
                  </span>

                </div>


                {/* DESCRIPTION */}
                <div className="sentinel-alert-description">
                  {alert.description}
                </div>


                {/* DEPARTMENTS */}
                <div className="sentinel-alert-departments">

                  {alert.departments.map(department => (

                    <span
                      key={department}
                      className="sentinel-department-tag"
                    >
                      {department}
                    </span>

                  ))}

                </div>

              </div>

            </button>

          ))

        )}

      </div>

    </aside>
  );
}

export default AlertsSidebar;