function MeetingCard({ meeting }) {

  return (

    <div className="meeting-card">

      <h3>
        {meeting.file_name}
      </h3>

      <p>

        <strong>
          Summary:
        </strong>

        {" "}
        {meeting.summary}

      </p>

      <p>

        <strong>
          Date:
        </strong>

        {" "}
        {meeting.created_at}

      </p>

    </div>

  );
}

export default MeetingCard;