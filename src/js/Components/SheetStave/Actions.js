import React from 'react';
import PropTypes from 'prop-types';

import SheetActions from 'omrActions/Sheet';

import Action from 'omrComponents/Common/ActionButton';

class Actions extends React.Component{
 componentDidMount(){
  const { store } = this.context;
  this.unsubscribe = store.subscribe(() =>
    this.forceUpdate()
  );
 }
 componentWillUnmount(){
  this.unsubscribe();
 }
 render(){
  const { store } = this.context;
  return(
   <div className="col-xs-3 sheet__actions actions">
    <Action className="actions__action" text="Merge Section" onClick={() => {
      console.log(store.getState());
      store.dispatch({ type: SheetActions.MERGE_STAVE_SECTIONS });
     }
    }/>;
   </div>
  );
 }
}

Actions.contextTypes = {
 store: PropTypes.object
}

export default Actions;