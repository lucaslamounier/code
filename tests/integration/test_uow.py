# pylint: disable=no-member
import pytest
from allocation.domain import model
from allocation.service_layer import unit_of_work
from djangoproject.alloc import models as django_models


def insert_batch(ref, sku, qty, eta):
    django_models.Batch.objects.create(reference=ref, sku=sku, qty=qty, eta=eta)


def get_allocated_batch_ref(orderid, sku):
    print(django_models.Allocation.objects.all())
    return django_models.Allocation.objects.get(
        line__orderid=orderid, line__sku=sku
    ).batch.reference


@pytest.mark.django_db(transaction=True)
def test_uow_can_retrieve_a_batch_and_allocate_to_it():
    insert_batch('batch1', 'HIPSTER-WORKBENCH', 100, None)

    uow = unit_of_work.DjangoUnitOfWork()
    with uow:
        batch = uow.batches.get(reference='batch1')
        line = model.OrderLine('o1', 'HIPSTER-WORKBENCH', 10)
        batch.allocate(line)
        uow.commit()

    batchref = get_allocated_batch_ref('o1', 'HIPSTER-WORKBENCH')
    assert batchref == 'batch1'


@pytest.mark.django_db(transaction=True)
def test_rolls_back_uncommitted_work_by_default():
    uow = unit_of_work.DjangoUnitOfWork()
    with uow:
        insert_batch('batch1', 'MEDIUM-PLINTH', 100, None)

    rows = django_models.Batch.objects.all()
    assert list(rows) == []


@pytest.mark.django_db(transaction=True)
def test_rolls_back_on_error():
    class MyException(Exception):
        pass

    uow = unit_of_work.DjangoUnitOfWork()
    with pytest.raises(MyException):
        with uow:
            insert_batch('batch1', 'LARGE-FORK', 100, None)
            raise MyException()

    rows = django_models.Batch.objects.all()
    assert list(rows) == []
