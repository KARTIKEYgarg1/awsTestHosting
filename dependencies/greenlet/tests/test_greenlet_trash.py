# -*- coding: utf-8 -*-
"""
Tests for greenlets interacting with the CPython trash can API.

The CPython trash can API is not designed to be re-entered from a
single thread. But this can happen using greenlets, if something
during the object deallocation process switches greenlets, and this second
greenlet then causes the trash can to get entered again. Here, we do this
very explicitly, but in other cases (like gevent) it could be arbitrarily more
complicated: for example, a weakref callback might try to acquire a lock that's
already held by another greenlet; that would allow a greenlet switch to occur.

See https://github.com/gevent/gevent/issues/1909

This test is fragile and relies on details of the CPython
implementation (like most of the rest of this package):

    - We enter the trashcan and deferred deallocation after
      ``_PyTrash_UNWIND_LEVEL`` calls. This constant, defined in
      CPython's object.c, is generally 50. That's basically how many objects are required to
      get us into the deferred deallocation situation.

    - The test fails by hitting an ``assert()`` in object.c; if the
      build didn't enable assert, then we don't catch this.

    - If the test fails in that way, the interpreter crashes.
"""
from __future__ import print_function, absolute_import, division

import unittest

class TestTrashCanReEnter(unittest.TestCase):

    def test_it(self):
        # Try several times to trigger it, because it isn't 100%
        # reliable.
        for _ in range(10):
            self.check_it()

    def check_it(self): # pylint:disable=too-many-statements
        import greenlet
        from greenlet._greenlet import get_tstate_trash_delete_nesting # pylint:disable=no-name-in-module

        main = greenlet.getcurrent()

        assert get_tstate_trash_delete_nesting() == 0

        # We expect to be in deferred deallocation after this many
        # deallocations have occurred. TODO: I wish we had a better way to do
        # this --- that was before get_tstate_trash_delete_nesting; perhaps
        # we can use that API to do better?
        TRASH_UNWIND_LEVEL = 50
        # How many objects to put in a container; it's the container that
        # queues objects for deferred deallocation.
        OBJECTS_PER_CONTAINER = 500

        class Dealloc: # define the class here because we alter class variables each time we run.
            """
            An object with a ``__del__`` method. When it starts getting deallocated
            from a deferred trash can run, it switches greenlets, allocates more objects
            which then also go in the trash can. If we don't save state appropriately,
            nesting gets out of order and we can crash the interpreter.
            """

            #: Has our deallocation actually run and switched greenlets?
            #: When it does, this will be set to the current greenlet. This should
            #: be happening in the main greenlet, so we check that down below.
            SPAWNED = False

            #: Has the background greenlet run?
            BG_RAN = False

            BG_GLET = None

            #: How many of these things have ever been allocated.
            CREATED = 0

            #: How many of these things have ever been deallocated.
            DESTROYED = 0

            #: How many were destroyed not in the main greenlet. There should always
            #: be some.
            #: If the test is broken or things change in the trashcan implementation,
            #: this may not be correct.
            DESTROYED_BG = 0

            def __init__(self, sequence_number):
                """
                :param sequence_number: The ordinal of this object during
                   one particular creation run. This is used to detect (guess, really)
                   when we have entered the trash can's deferred deallocation.
                """
                self.i = sequence_number
                Dealloc.CREATED += 1

            def __del__(self):
                if self.i == TRASH_UNWIND_LEVEL and not self.SPAWNED:
                    Dealloc.SPAWNED = greenlet.getcurrent()
                    other = Dealloc.BG_GLET = greenlet.greenlet(background_greenlet)
                    x = other.switch()
                    assert x == 42
                    # It's important that we don't switch back to the greenlet,
                    # we leave it hanging there in an incomplete state. But we don't let it
                    # get collected, either. If we complete it now, while we're still
                    # in the scope of the initial trash can, things work out and we
                    # don't see the problem. We need this greenlet to complete
                    # at some point in the future, after we've exited this trash can invocation.
                    del other
                elif self.i == 40 and greenlet.getcurrent() is not main:
                    Dealloc.BG_RAN = True
                    try:
                        main.switch(42)
                    except greenlet.GreenletExit as ex:
                        # We expect this; all references to us go away
                        # while we're still running, and we need to finish deleting
                        # ourself.
                        Dealloc.BG_RAN = type(ex)
                        del ex

                # Record the fact that we're dead last of all. This ensures that
                # we actually get returned too.
                Dealloc.DESTROYED += 1
                if greenlet.getcurrent() is not main:
                    Dealloc.DESTROYED_BG += 1


        def background_greenlet():
            # We direct through a second function, instead of
            # directly calling ``make_some()``, so that we have complete
            # control over when these objects are destroyed: we need them
            # to be destroyed in the context of the background greenlet
            t = make_some()
            del t # Triggere deletion.

        def make_some():
            t = ()
            i = OBJECTS_PER_CONTAINER
            while i:
                # Nest the tuples; it's the recursion that gets us
                # into trash.
                t = (Dealloc(i), t)
                i -= 1
            return t


        some = make_some()
        self.assertEqual(Dealloc.CREATED, OBJECTS_PER_CONTAINER)
        self.assertEqual(Dealloc.DESTROYED, 0)

        # If we're going to crash, it should be on the following line.
        # We only crash if ``assert()`` is enabled, of course.
        del some

        # For non-debug builds of CPython, we won't crash. The best we can do is check
        # the nesting level explicitly.
        self.assertEqual(0, get_tstate_trash_delete_nesting())

        # Discard this, raising GreenletExit into where it is waiting.
        Dealloc.BG_GLET = None
        # The same nesting level maintains.
        self.assertEqual(0, get_tstate_trash_delete_nesting())

        # We definitely cleaned some up in the background
        self.assertGreater(Dealloc.DESTROYED_BG, 0)

        # Make sure all the cleanups happened.
        self.assertIs(Dealloc.SPAWNED, main)
        self.assertTrue(Dealloc.BG_RAN)
        self.assertEqual(Dealloc.BG_RAN, greenlet.GreenletExit)
        self.assertEqual(Dealloc.CREATED, Dealloc.DESTROYED )
        self.assertEqual(Dealloc.CREATED, OBJECTS_PER_CONTAINER * 2)

        import gc
        gc.collect()


if __name__ == '__main__':
    unittest.main()
