import uuid
import pytest
import pytest_asyncio
from sqlalchemy import insert, update
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import JSONResponse
from fastapi import HTTPException
from typing import Tuple, Any

from database.models import Todo, User
from routes.todo.t_creation import TodoCreation
from routes.todo.t_validation_model import TodoCreationModel, TodoExistCheckModel, HandleTodoRequestModel
from routes.todo.t_utils import (
    todo_exists, TodoExistCheckModel,
    run_todo_db_statement, RunTodoDbStatementContext,
    handle_todo_request
)
from security.jwt import create_token


class TestTodoExists:
    """ Test class for different scenarios for the todo_exists function """

    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, fake_todo: Tuple[Todo, User, AsyncSession]) -> None:
        """ Set up common test data """
        self.todo, self.user, self.db_session = fake_todo

        # Define differnt data models
        self.data_for_title = TodoExistCheckModel(user_id=self.user.id, title=self.todo.title)
        self.data_for_todoID = TodoExistCheckModel(user_id=self.user.id, todo_id=self.todo.id)
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize("data_type", [("title"), ("todo_id")])
    async def test_todo_exists_success(self, data_type: str) -> None:
        """ Tests the search for the todo with the title or todo id """
        if data_type == "title":
            exists = await todo_exists(data=self.data_for_title, db_session=self.db_session)
        elif data_type == "todo_id":
            exists = await todo_exists(data=self.data_for_todoID, db_session=self.db_session)

        assert exists

    @pytest.mark.asyncio
    @pytest.mark.parametrize("data_type", [("title"), ("todo_id")])
    async def test_todo_exists_failed_because_todo_does_not_exist(self, data_type: str) -> None:
        """ Tests the failed case if the todo does not exist """
        if data_type == "title":
            self.data_for_title.todo_id = uuid.uuid4()
            exists = await todo_exists(data=self.data_for_title, db_session=self.db_session)
        elif data_type == "todo_id":
            self.data_for_todoID.todo_id = uuid.uuid4()
            exists = await todo_exists(data=self.data_for_todoID, db_session=self.db_session)

        assert not exists

    @pytest.mark.asyncio
    async def test_todo_exists_failed_because_db_session_is_invalid(self) -> None:
        """ Tests the failed case if the database session is invalid """
        with pytest.raises(ValueError):
            await todo_exists(data=self.data_for_title, db_session="Broken Database Session")


class TestRunTodoDbStatement:
    """ Test class for different scenarios for the run_todo_db_statement function """

    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, fake_todo: Tuple[Todo, User, AsyncSession]) -> None:
        """ Set up common test data """
        self.todo, self.user, self.db_session = fake_todo

        # Default test data
        self.title: str = "Fake Todo"
        self.description: str = "A fake description"
        self.db_insert_statement = (
            insert(Todo)
            .values(user_id=self.user.id, title=self.title, description=self.description)
            .returning(Todo)
        )
        self.success_msg: str = "Todo successful created."
        self.default_error_msg: str = "Server error occurred."
        self.execution_type: str = "Insertion"


    @pytest.mark.asyncio
    @pytest.mark.parametrize("should_todo_exist", [(True), (False)])
    async def test_run_todo_db_statement_success(self, should_todo_exist: bool) -> None:
        """ Tests the success case with creating a new todo """
        success, msg = await run_todo_db_statement(
            ctx=RunTodoDbStatementContext(
                data=TodoExistCheckModel(
                    user_id=self.user.id,
                    title=self.title # Todo with this title does not exist, right now
                ),
                db_statement=self.db_insert_statement,
                db_session=self.db_session,
                success_msg=self.success_msg,
                default_error_msg=self.default_error_msg,
                execution_type=self.execution_type,
                should_todo_exist=should_todo_exist
            )
        )
        
        # Reminder:
        # We're simulating an INSERT operation, so the todo should *not* exist.

        # Case 1: should_todo_exist = True
        # -> Fails, because the todo is NOT in the DB -> success = False

        # Case 2: should_todo_exist = False
        # -> Proceeds, todo is inserted -> success = True

        # So: success is always the opposite of should_todo_exist
        assert success != should_todo_exist


    @pytest.mark.asyncio
    async def test_run_todo_db_statement_failed_because_todo_does_not_exist(self) -> None:
        """ Tests the failed case if the todo does not exist """
        success, msg = await run_todo_db_statement(
            ctx=RunTodoDbStatementContext(
                data=TodoExistCheckModel(
                    user_id=self.user.id,
                    todo_id=uuid.uuid4() # Invalid todo id
                ),
                db_statement=self.db_insert_statement,
                db_session=self.db_session,
                success_msg=self.success_msg,
                default_error_msg=self.default_error_msg,
                execution_type=self.execution_type,
                should_todo_exist=True
            )
        )

        # Since the todo with the specified todo id does not exist, False is expected.
        # Important: Although we are using the insert db statement here, 
        # this is irrelevant for this test, as it does not add anything because the Todo 
        # does not exist and is aborted beforehand.
        assert not success


    @pytest.mark.asyncio
    async def test_run_todo_db_statement_failed_because_unknown_error(self) -> None:
        """ Tests the failed case if the execution is failed for an unknown reason """
        # For simplicity, it is tested with an update statement.
        db_update_statement = (
            update(Todo)
            .where(Todo.user_id == self.user.id, Todo.id == uuid.uuid4())
            .values(title=self.title, description=self.description)
            .returning(Todo)
        )
        
        success, msg = await run_todo_db_statement(
            ctx=RunTodoDbStatementContext(
                data=TodoExistCheckModel(
                    user_id=self.user.id,
                    todo_id=self.todo.id
                ),
                db_statement=db_update_statement,
                db_session=self.db_session,
                success_msg=self.success_msg,
                default_error_msg=self.default_error_msg,
                execution_type="Update",
                should_todo_exist=False # Deliberately set False to provoke the error that the 
                # todo cannot be updated because it does not exist.
            )
        )

        assert not success

    
    @pytest.mark.asyncio
    @pytest.mark.parametrize("invalid_user, invalid_db_session", [(True, False), (False, True)])
    async def test_run_todo_db_statement_failed_because_database_error(
        self, invalid_user: bool, invalid_db_session: bool
    ) -> None:
        """ Tests the failed case if the database has problems and a database error occurred """
        db_statement = self.db_insert_statement
        db_session = self.db_session

        if invalid_user:
            # Indicates an unregistered user
            db_statement = (
                insert(Todo)
                .values(
                    user_id=uuid.uuid4(), # <- invalid user id (FOREIGN KEY constraint failed)
                    title=self.title, description=self.description)
                .returning(Todo)
            )
        elif invalid_db_session:
            # Invalidates the database session
            from unittest.mock import AsyncMock
            from sqlalchemy.exc import SQLAlchemyError

            broken_session = AsyncMock(wraps=db_session)
            broken_session.__class__ = AsyncSession
            broken_session.execute.side_effect = SQLAlchemyError("Broken Database Session")
            db_session = broken_session

        success, msg = await run_todo_db_statement(
            ctx=RunTodoDbStatementContext(
                data=TodoExistCheckModel(
                    user_id=self.user.id,
                    todo_id=self.todo.id # Irrelevant (but must be set, otherwise a validation error will occur)
                ),
                db_statement=db_statement,
                db_session=db_session,
                success_msg=self.success_msg,
                default_error_msg=self.default_error_msg,
                execution_type=self.execution_type,
                should_todo_exist=False
            )
        )

        assert not success


class TestHandleTodoRequest:
    """ Test class for different scenarios for the handle_todo_request method """

    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, fake_user: Tuple[User, AsyncSession]) -> None:
        """ Set up common test data """
        self.user, self.db_session = fake_user

        # Define test values
        self.token: str = create_token(data={"sub": str(self.user.id)})
        self.data_model = TodoCreationModel(title="A test title", description="A test description")
        self.service_class = TodoCreation
        self.service_method: str = "create"
        self.default_error_message: str = "An unexpected server error occurred."

    @pytest.mark.asyncio
    async def test_handle_todo_request_success(self) -> None:
        """ Tests the success case of this method """
        response: JSONResponse = await handle_todo_request(
            data_model=self.data_model, db_session=self.db_session, 
            params=HandleTodoRequestModel(
                token=self.token, service_class=self.service_class,
                service_method=self.service_method,
                default_error_message=self.default_error_message,
            )
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_handle_todo_request_failed_because_not_success(self) -> None:
        """ Tests the failed case if the success state is False """
        failed_msg: str = "Creation failed: An unexpected error occurred."

        class TestFailedClass:
            def __init__(self, data: Any, db_session: AsyncSession, user_id: uuid.UUID): 
                pass

            async def create(self):
                return (False, failed_msg)

        # Expect an exception
        with pytest.raises(HTTPException) as exc_info:
            await handle_todo_request(
                data_model=self.data_model, db_session=self.db_session, 
                params=HandleTodoRequestModel(
                    token=self.token, service_class=TestFailedClass,
                    service_method=self.service_method,
                    default_error_message=failed_msg,
                )
            )
        
        # Tests the output
        exception = exc_info.value
        assert exception.status_code == 400
        assert exception.detail == failed_msg


    @pytest.mark.asyncio
    @pytest.mark.parametrize("invalid_db_session, invalid_token", [(True, False), (False, True)])
    async def test_handle_todo_request_failed_because_value_error(
        self, invalid_db_session: bool, invalid_token: bool
    ) -> None:
        """ Tests the failed case if a ValueError occurrs """
        db_session = self.db_session
        token = self.token

        if invalid_db_session:
            db_session = "Invalid db session" # <- triggers a ValueError (no open and valid db session)
        elif invalid_token:
            token = create_token({"no_sub": str(self.user.id)}) # <- triggers a ValueError (no sub exists) 

        with pytest.raises(HTTPException) as exc_info:
            await handle_todo_request(
                data_model=self.data_model, db_session=db_session, 
                params=HandleTodoRequestModel(
                    token=token,
                    service_class=self.service_class,
                    service_method=self.service_method,
                    default_error_message=self.default_error_message,
                )
            )

        assert exc_info.value.status_code == 400

    
    @pytest.mark.asyncio
    async def test_handle_todo_request_failed_because_validation_error(self) -> None:
        """ Tests the failed case if a validation error occurrs """
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            await handle_todo_request(
                data_model=self.data_model, db_session=self.db_session, 
                params=HandleTodoRequestModel(
                    token=int(0), # <- triggers a ValidationError
                    service_class=self.service_class,
                    service_method=self.service_method,
                    default_error_message=self.default_error_message,
                )
            )