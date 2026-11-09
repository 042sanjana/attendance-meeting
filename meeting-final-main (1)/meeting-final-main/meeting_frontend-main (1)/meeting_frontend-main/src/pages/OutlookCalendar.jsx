import React,
{
  useEffect,
  useState
}
from "react";

import axios from "axios";

import Calendar
from "react-calendar";

import "react-calendar/dist/Calendar.css";

import "./OutlookCalendar.css";

function OutlookCalendar() {

  const [tasks,
    setTasks] =
    useState([]);

  const [selectedDate,
    setSelectedDate] =
    useState(new Date());

  useEffect(() => {

    fetchTasks();

  }, []);

  const fetchTasks =
    async () => {

      try {

        const user =
          JSON.parse(
            localStorage.getItem(
              "user"
            )
          );

        const response =
          await axios.get(
            `http://127.0.0.1:8000/meetings/user/${user.id}/tasks`
          );

        setTasks(
          response.data
        );

      } catch (error) {

        console.log(error);

      }

    };

  const formatDate =
    (date) => {

      const y =
        date.getFullYear();

      const m =
        String(
          date.getMonth() + 1
        ).padStart(2, "0");

      const d =
        String(
          date.getDate()
        ).padStart(2, "0");

      return `${y}-${m}-${d}`;

    };

  const tileContent =
    ({ date, view }) => {

      if (
        view !== "month"
      )
        return null;

      const current =
        formatDate(date);

      const count =
        tasks.filter(
          task =>
            task.deadline_date?.substring(
              0,
              10
            ) === current
        ).length;

      return count > 0 ? (

        <div
          className="task-count"
        >
          {count}
        </div>

      ) : null;

    };

  const selected =
    formatDate(
      selectedDate
    );

  const filteredTasks =
    tasks.filter(
      task =>
        task.deadline_date?.substring(
          0,
          10
        ) === selected
    );

  return (

    <div className="outlook-page">

      <h1>
        📆 Outlook Calendar
      </h1>

      <Calendar
        value={
          selectedDate
        }
        onChange={
          setSelectedDate
        }
        tileContent={
          tileContent
        }
      />

      <h2>
        Tasks Due On:
        {" "}
        {selected}
      </h2>

      {filteredTasks.length >
      0 ? (

        filteredTasks.map(
          task => (

            <div
              key={task.id}
              className="task-card"
            >

              <h3>
                {task.task}
              </h3>

              <p>
                Owner:
                {" "}
                {task.owner}
              </p>

              <p>
                Priority:
                {" "}
                {task.priority}
              </p>

              <p>
                Status:
                {" "}
                {task.status}
              </p>

            </div>

          )
        )

      ) : (

        <p>
          No tasks for
          this date
        </p>

      )}

    </div>

  );

}

export default OutlookCalendar;