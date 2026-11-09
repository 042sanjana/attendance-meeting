import { useEffect } from "react";
import { useParams } from "react-router-dom";
import { useState } from "react";

import API from "../services/api";

function MeetingDetails() {

  const { id } = useParams();

  const [meeting, setMeeting] =
    useState(null);

  useEffect(() => {

    loadMeeting();

  }, []);

  const loadMeeting = async () => {

    try {

      const response =
        await API.get(
          `/meeting/${id}`
        );

      setMeeting(
        response.data
      );

    } catch(error) {

      console.log(error);

    }
  };

  if (!meeting) {

    return (
      <h2>
        Loading...
      </h2>
    );
  }

  return (

    <div>

      <h1>
        {meeting.file_name}
      </h1>

      <h3>
        Transcript
      </h3>

      <p>
        {meeting.transcript}
      </p>

      <h3>
        Summary
      </h3>

      <p>
        {meeting.summary}
      </p>

    </div>

  );
}

export default MeetingDetails;