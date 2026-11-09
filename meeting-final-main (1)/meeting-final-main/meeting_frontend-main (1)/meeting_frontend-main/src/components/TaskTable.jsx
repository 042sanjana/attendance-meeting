import React, {
  useEffect,
  useState
} from "react";

import axios from "axios";

import "./TaskTable.css";

function TaskTable() {

  const [tasks, setTasks] =
    useState([]);

  useEffect(() => {

    fetchTasks();

  }, []);

  const fetchTasks = async () => {
  try {

    const user = JSON.parse(
      localStorage.getItem("user")
    );

    console.log("USER =", user);

    const response = await axios.get(
      `http://127.0.0.1:8000/meetings/user/${user.id}/tasks`
    );

    console.log(
      "TASKS RECEIVED =",
      response.data
    );

    setTasks(response.data);

  } catch (error) {

    console.log(
      "ERROR =",
      error
    );

  }
};
  return (

    <div className="task-table-container">

      <h2>
        📋 My Tasks
      </h2>

      <table className="task-table">

        <thead>

          <tr>

            <th>
              Owner
            </th>

            <th>
              Task
            </th>

            <th>
              Deadline
            </th>

            <th>
              Status
            </th>

          </tr>

        </thead>

        <tbody>

          {tasks.length > 0 ? (

            tasks.map(task => (

              <tr
                key={task.id}
              >

                <td>
                  {task.owner}
                </td>

                <td>
                  {task.task}
                </td>

                <td>
                  {task.deadline_date}
                </td>

                <td>

                  <span
                    className={
                      task.status ===
                      "Completed"
                        ? "completed"
                        : task.status ===
                          "In Progress"
                        ? "progress"
                        : "pending"
                    }
                  >

                    {task.status}

                  </span>

                </td>

              </tr>

            ))

          ) : (

            <tr>

              <td
                colSpan="4"
              >

                No Tasks Found

              </td>

            </tr>

          )}

        </tbody>

      </table>

    </div>

  );

}

export default TaskTable;